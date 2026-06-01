"""
Read StaticDataLocalization from Raid: Shadow Legends via Il2CppDumper offsets.
No DLL injection — uses ReadProcessMemory only.

Chain:
  GameAssembly.dll + SharedModelManager_TypeInfo_RVA
    → Il2CppClass* for SharedModelManager
    → Il2CppClass.static_fields (offset 0xB8)
    → StaticData* (offset 0x8 in static storage)
    → ClientStaticData.StaticDataLocalization (offset 0x1C0)
    → Dictionary<string,string> entries

Requires: Raid running, Admin rights.
Output: tools/l10n-from-memory.json
"""
import ctypes
import ctypes.wintypes as wt
import struct
import sys
import json
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── From Il2CppDumper output ──────────────────────────────────────────
SHARED_MODEL_MANAGER_TYPEINFO_RVA = 0x4E6C058  # SharedModel.SharedModelManager_TypeInfo
STATIC_DATA_FIELD_OFFSET          = 0x08       # StaticData field in SharedModelManager static storage
STATIC_DATA_LOCALIZATION_OFFSET   = 0x1C0      # ClientStaticData.StaticDataLocalization (Dictionary)
IL2CPP_CLASS_STATIC_FIELDS_OFFSET = 0xB8       # static_fields pointer in Il2CppClass

# Il2Cpp managed object header: klass* (8) + monitor* (8) = 16 bytes before content
OBJ_HEADER = 16

# ── Windows API ───────────────────────────────────────────────────────
PROCESS_VM_READ           = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
k32 = ctypes.windll.kernel32


def find_pid(name: str) -> int:
    out = subprocess.check_output(
        ["powershell", "-Command",
         f"Get-Process -Name '{name}' | Select-Object -First 1 -ExpandProperty Id"],
        text=True, errors="replace",
    ).strip()
    return int(out) if out.isdigit() else 0


def read_ptr(handle, addr: int) -> int:
    buf = ctypes.create_string_buffer(8)
    read = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, 8, ctypes.byref(read))
    if ok and read.value == 8:
        return struct.unpack_from("<Q", buf)[0]
    return 0


def read_bytes(handle, addr: int, size: int) -> bytes | None:
    buf = ctypes.create_string_buffer(size)
    read = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, size, ctypes.byref(read))
    return buf.raw[:read.value] if ok and read.value > 0 else None


def read_il2cpp_string(handle, obj_ptr: int) -> str | None:
    """Read IL2Cpp managed String object: OBJ_HEADER + 4-byte length + UTF-16 chars."""
    if not obj_ptr or obj_ptr < 0x10000:
        return None
    hdr = read_bytes(handle, obj_ptr + OBJ_HEADER, 4)
    if not hdr:
        return None
    length = struct.unpack_from("<I", hdr)[0]
    if length == 0 or length > 2048:
        return None
    chars = read_bytes(handle, obj_ptr + OBJ_HEADER + 4, length * 2)
    if not chars:
        return None
    try:
        return chars.decode("utf-16-le")
    except Exception:
        return None


def find_module_base(handle, pid: int, module_name: str) -> int:
    """Find base address of a module in the process."""
    import ctypes.wintypes as wt

    class MODULEENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize",        wt.DWORD),
            ("th32ModuleID",  wt.DWORD),
            ("th32ProcessID", wt.DWORD),
            ("GlblcntUsage",  wt.DWORD),
            ("ProccntUsage",  wt.DWORD),
            ("modBaseAddr",   ctypes.POINTER(wt.BYTE)),
            ("modBaseSize",   wt.DWORD),
            ("hModule",       wt.HMODULE),
            ("szModule",      ctypes.c_char * 256),
            ("szExePath",     ctypes.c_char * 260),
        ]

    TH32CS_SNAPMODULE = 0x00000008
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
    if not snap:
        return 0

    me = MODULEENTRY32()
    me.dwSize = ctypes.sizeof(MODULEENTRY32)
    target = module_name.lower().encode()

    try:
        if k32.Module32First(snap, ctypes.byref(me)):
            while True:
                if target in me.szModule.lower():
                    return ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value
                if not k32.Module32Next(snap, ctypes.byref(me)):
                    break
    finally:
        k32.CloseHandle(snap)
    return 0


def read_dictionary(handle, dict_ptr: int) -> dict[str, str]:
    """
    Read IL2Cpp Dictionary<string, string> entries.
    Layout (after OBJ_HEADER):
      +0x00  Il2CppClass* klass (already consumed in OBJ_HEADER)
      Actually: entries are in _entries array → each entry: hash(4)+next(4)+key_ptr(8)+val_ptr(8)
    """
    # Dictionary<K,V> managed layout (after 16-byte obj header):
    # 0x00: buckets (Il2CppArray*)
    # 0x08: entries (Il2CppArray*)
    # 0x10: count (int32)
    base = dict_ptr + OBJ_HEADER
    entries_arr_ptr = read_ptr(handle, base + 0x08)
    count = read_bytes(handle, base + 0x10, 4)
    if not count:
        return {}
    count = struct.unpack_from("<I", count)[0]
    if count == 0 or count > 100000:
        return {}

    # Il2CppArray: OBJ_HEADER(16) + bounds_ptr(8) + max_length(8) = 32 bytes before data
    ARRAY_HEADER = 32
    # Each entry: hash(int32) + next(int32) + key*(int64) + value*(int64) = 24 bytes
    ENTRY_SIZE = 24

    result = {}
    for i in range(count):
        entry_addr = entries_arr_ptr + ARRAY_HEADER + i * ENTRY_SIZE
        data = read_bytes(handle, entry_addr, ENTRY_SIZE)
        if not data or len(data) < ENTRY_SIZE:
            continue
        key_ptr = struct.unpack_from("<Q", data, 8)[0]
        val_ptr = struct.unpack_from("<Q", data, 16)[0]
        if not key_ptr or not val_ptr:
            continue
        key = read_il2cpp_string(handle, key_ptr)
        val = read_il2cpp_string(handle, val_ptr)
        if key and val:
            result[key] = val

    return result


def main():
    pid = find_pid("Raid")
    if not pid:
        sys.exit("ERROR: Raid not running")
    print(f"Raid PID: {pid}")

    handle = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        sys.exit(f"ERROR: OpenProcess failed ({k32.GetLastError()}). Run as Admin.")

    # Step 1: Find GameAssembly.dll base
    ga_base = find_module_base(handle, pid, "GameAssembly.dll")
    if not ga_base:
        sys.exit("ERROR: GameAssembly.dll not found in process modules")
    print(f"GameAssembly.dll base: 0x{ga_base:016x}")

    # Step 2: Read SharedModelManager_TypeInfo pointer
    typeinfo_addr = ga_base + SHARED_MODEL_MANAGER_TYPEINFO_RVA
    typeinfo_ptr = read_ptr(handle, typeinfo_addr)
    print(f"SharedModelManager TypeInfo: 0x{typeinfo_ptr:016x}")
    if not typeinfo_ptr:
        sys.exit("ERROR: TypeInfo pointer is null")

    # Step 3: Read static_fields from Il2CppClass
    static_fields_ptr = read_ptr(handle, typeinfo_ptr + IL2CPP_CLASS_STATIC_FIELDS_OFFSET)
    print(f"SharedModelManager static_fields: 0x{static_fields_ptr:016x}")
    if not static_fields_ptr:
        sys.exit("ERROR: static_fields is null (game not fully loaded?)")

    # Step 4: Read StaticData pointer (offset 0x8 in static storage)
    static_data_ptr = read_ptr(handle, static_fields_ptr + STATIC_DATA_FIELD_OFFSET)
    print(f"StaticData object: 0x{static_data_ptr:016x}")
    if not static_data_ptr:
        sys.exit("ERROR: StaticData is null (not loaded yet?)")

    # Step 5: Read StaticDataLocalization dictionary (offset 0x1C0 from object start)
    # NOTE: dump.cs offsets include the 16-byte Il2CppObject header — no need to add OBJ_HEADER
    dict_ptr = read_ptr(handle, static_data_ptr + STATIC_DATA_LOCALIZATION_OFFSET)
    print(f"StaticDataLocalization dict: 0x{dict_ptr:016x}")
    if not dict_ptr:
        sys.exit("ERROR: Dictionary pointer is null")

    # Step 6: Read dictionary entries
    print("Reading l10n dictionary...")
    l10n = read_dictionary(handle, dict_ptr)
    print(f"Entries read: {len(l10n)}")

    k32.CloseHandle(handle)

    if not l10n:
        sys.exit("ERROR: No entries read — check offsets or game loading state")

    # Verify a known entry
    test = l10n.get("l10n:hero-type/name?id=5780#static")
    print(f"Astralon name: {test}")

    out = Path(__file__).parent / "l10n-from-memory.json"
    out.write_text(json.dumps(l10n, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {len(l10n)} entries to {out}")


if __name__ == "__main__":
    main()
