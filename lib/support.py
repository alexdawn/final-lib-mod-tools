from utilities import check_eof
from flags import nationalities, unit_types, support_flags


def read_support(file):
    supports = []

    header = file.read(13)
    if header != b'SUPPORT\x00\x001.0\x00':
        raise RuntimeError("File is not a SUPPORT.DAT")
    count = int.from_bytes(file.read(4), 'little')
    for i in range(count):
        cid = int.from_bytes(file.read(2), 'little')
        flags = int.from_bytes(file.read(4), 'little')
        if flags & (0xffff - 0x600b) != 0:
            raise RuntimeError(f"Unknown flag, {cid} {flags}")
        flag_text = []
        for f, v in support_flags.items():
            if f & flags:
                flag_text.append(v)
        licon = int.from_bytes(file.read(4), 'little')
        ricon = int.from_bytes(file.read(4), 'little')
        nation = int.from_bytes(file.read(4), 'little')
        string_length1 = int.from_bytes(file.read(1), 'little')
        string1 = bytes(file.read(string_length1)).decode('utf-8')
        string_length2 = int.from_bytes(file.read(1), 'little')
        string2 = bytes(file.read(string_length2)).decode('utf-8')
        cost = int.from_bytes(file.read(2), 'little')
        breakpoint = int.from_bytes(file.read(1), 'little')
        # TODO handle special morale values
        #define CLAN_MORALE						-1
        #define MORALE_SPECIAL					-2
        #define ALLWAYS_PASS_MORALE			0
        morale = int.from_bytes(file.read(1), 'little', signed=True)
        vp = int.from_bytes(file.read(1), 'little')
        u_count = int.from_bytes(file.read(1), 'little')
        allow_nation = int.from_bytes(file.read(4), 'little') # allow nat flag
        nation_flags = []
        for f, v in nationalities.items():
            if f & allow_nation:
                nation_flags.append(v)
        allow_type = int.from_bytes(file.read(4), 'little') # allow type flag
        allow_type_flags = []
        for f, v in unit_types.items():
            if f & allow_type:
                allow_type_flags.append(v)
        turns_to_build = int.from_bytes(file.read(2), 'big')
        uids = [
            int.from_bytes(file.read(2), 'little')
            for i in range(u_count)
        ]
        #unames = [unit_lookup[x] for x in uids]
        #detachments[cid] = string1
        supports.append({
            "id": cid,
            "name1": string1,
            "name2": string2,
            "cost": cost,
            "breakpoint": breakpoint,
            "morale": morale,
            "victory_points": vp,
            "units": uids,
            "flags": flag_text,
            "licon": licon,
            "ricon": ricon,
            "nation": nation,
            "allow_nation": nation_flags,
            "type": allow_type_flags,
            "time_to_build": turns_to_build
        })
    check_eof(file)
    return supports


def write_support(file, data):
    support_flags_lookups = {v: k for k, v in support_flags.items()}
    nationalities_lookup = {v: k for k, v in nationalities.items()}
    unit_types_lookup = {v: k for k, v in unit_types.items()}
    file.write(b'SUPPORT\x00\x001.0\x00')
    file.write(len(data).to_bytes(4, 'little'))
    for d in data:
        file.write(d['id'].to_bytes(2, 'little'))
        #encode flags
        flag_value = 0
        for x in d['flags']:
            flag_value += support_flags_lookups[x]
        file.write(flag_value.to_bytes(4, 'little'))
        file.write(d['licon'].to_bytes(4, 'little'))
        file.write(d['ricon'].to_bytes(4, 'little'))
        file.write(d['nation'].to_bytes(4, 'little'))
        file.write(len(d['name1']).to_bytes(1, 'little'))
        file.write(d['name1'].encode('ascii'))
        file.write(len(d['name2']).to_bytes(1, 'little'))
        file.write(d['name2'].encode('ascii'))
        file.write(d['cost'].to_bytes(2, 'little'))
        file.write(d['breakpoint'].to_bytes(1, 'little'))
        file.write(d['morale'].to_bytes(1, 'little', signed=True))
        file.write(d['victory_points'].to_bytes(1, 'little'))
        file.write(len(d['units']).to_bytes(1, 'little'))
        # nation flag
        flag_value = 0
        for x in d['allow_nation']:
            flag_value += nationalities_lookup[x]
        file.write(flag_value.to_bytes(4, 'little'))
        # allow type flags
        flag_value = 0
        for x in d['type']:
            flag_value += unit_types_lookup[x]
        file.write(flag_value.to_bytes(4, 'little'))
        file.write(d['time_to_build'].to_bytes(2, 'big'))
        for u in d['units']:
            file.write(u.to_bytes(2, 'little'))
