from flags import unit_flags, Chassis, Criticals, Shields, Severity
from utilities import check_eof
# weapon_lookup.update(
#     {
#         -1: "WPID_SELECT",
#         -2: "WPID_NOTHING"
#     }
# )


def footprint_to_int(b):
    values = []
    for i in range(8):
        if 1 << i & b:
            values.append(i)
    return values


def footprint_from_int(f):
    bits = 0
    for i in f:
        bits += 1 << i
    return bits


def read_unit(file):
    units = []
    header = file.read(13)
    if header != b'UNITDATA\x001.0\x00':
        raise RuntimeError("File is not a UNIT.DAT file")
    count = int.from_bytes(file.read(4), 'little')
    for i in range(count):
        uid = int.from_bytes(file.read(2), 'little')
        shadow_id = int.from_bytes(file.read(2), 'little')
        flags = int.from_bytes(file.read(4), 'little')
        flag_text = []
        for f, v in unit_flags.items():
            if f & flags:
                flag_text.append(v)
        troop_transport = int.from_bytes(file.read(1), 'little')
        iid = int.from_bytes(file.read(4), 'little')  # icon id
        name_length = int.from_bytes(file.read(1), 'little')
        name = bytes(file.read(name_length)).decode('ascii')
        move = int.from_bytes(file.read(1), 'little')
        save = int.from_bytes(file.read(1), 'little')
        caf = int.from_bytes(file.read(1), 'little')
        armours = []
        for i in range(4):
            unknown = int.from_bytes(file.read(1), 'little')
            if unknown != 0:
                raise RuntimeError("Initial armour value should be zero")
            d6_value = int.from_bytes(file.read(1), 'little')
            armour_front = int.from_bytes(file.read(1), 'little')
            armour_side = int.from_bytes(file.read(1), 'little')
            armour_rear = int.from_bytes(file.read(1), 'little')
            hit_offset_x = int.from_bytes(file.read(2), 'little', signed=True)
            hit_offset_y = int.from_bytes(file.read(2), 'little', signed=True)
            hit_offset_z = int.from_bytes(file.read(2), 'little', signed=True)
            armours.append(
                (d6_value, armour_front, armour_side, armour_rear,
                (hit_offset_x, hit_offset_y, hit_offset_z)))
        chassis_type = Chassis(int.from_bytes(file.read(1), 'little'))
        weapon_slots = int.from_bytes(file.read(1), 'little')
        shield_type = Shields(int.from_bytes(file.read(1), 'little'))
        shields = int.from_bytes(file.read(1), 'little')
        hit_points = int.from_bytes(file.read(1), 'little')
        unit_cost = int.from_bytes(file.read(2), 'little')

        footprint = [
            footprint_to_int(int.from_bytes(file.read(1), 'little'))
            for i in range(8)
        ]
        crit_damage = int.from_bytes(file.read(1), 'little', signed=True)
        dx = int.from_bytes(file.read(1), 'little', signed=True)
        dy = int.from_bytes(file.read(1), 'little', signed=True)
        dz = int.from_bytes(file.read(1), 'little', signed=True)
        crits = []
        for i in range(11):
            crit_type = Criticals(
                int.from_bytes(file.read(1), 'little', signed=True)
            )
            crit_mode = Severity(
                int.from_bytes(file.read(1), 'little', signed=True)
            )
            var1 = int.from_bytes(file.read(1), 'little', signed=True)
            var2 = int.from_bytes(file.read(1), 'little', signed=True)
            crits.append(
                [str(crit_type), str(crit_mode), var1, var2]
            )

        # weaps
        weapons = []
        for i in range(weapon_slots):
            weapons.append(
                {
                    'weapon_id': int.from_bytes(
                        file.read(2), 'little', signed=True
                    )
                }
            )
            #weapons[i]['weapon_name'] = weapon_lookup.get(weapons[i]['weapon_id'], "INVALID ID")
        for i in range(weapon_slots):
            weapons[i]['weapon_count'] = int.from_bytes(file.read(1), 'little')
        for i in range(weapon_slots):
            weapons[i]['base_hit_chance'] = int.from_bytes(file.read(1), 'little')
        # are we sure these are sorted like this into triples?
        for i in range(weapon_slots):
            dx = int.from_bytes(file.read(1), 'little', signed=True)
            dy = int.from_bytes(file.read(1), 'little', signed=True)
            dz = int.from_bytes(file.read(1), 'little', signed=True)
            weapons[i]['offset'] = (dx, dy, dz)
            term = int.from_bytes(file.read(1), 'little', signed=True)
            if term != 0:
                raise RuntimeError(
                    "final byte in weapon slot should be zero"
                )
        start_of_secondary = int.from_bytes(file.read(2), 'little')
        start_of_missile = int.from_bytes(file.read(2), 'little')
        start_of_special = int.from_bytes(file.read(2), 'little')
        #unit_lookup[uid] = name
        units.append({
            "unit_id": uid,
            "shadow_id": shadow_id,
            "flags": flag_text,
            "icon_id": iid,
            "name": name,
            "move": move,
            "save": save,
            "caf": caf,
            "armour": armours,
            "chassis_type": str(chassis_type),
            "weapons": weapons,
            "shield_type": str(shield_type),
            "shields": shields,
            "hit_points": hit_points,
            "unit_cost": unit_cost,
            "crit_damage": crit_damage,
            "crit_pos": [dx, dy, dz],
            "crits": crits, #if 'FLAG_UNIT_HAS_CRITS' in flag_text else [],
            "footprint": footprint, #if 'FLAG_HAS_FOOTPRINT' in flag_text else [],
            "start_of_secondary": start_of_secondary,
            "start_of_missile": start_of_missile,
            "start_of_special": start_of_special,
            "troop_transport": troop_transport,
        })
    check_eof(file)
    return units


def write_unit(file, data):
    unit_flag_lookups = {v: k for k, v in unit_flags.items()}

    file.write(b'UNITDATA\x001.0\x00')
    file.write(len(data).to_bytes(4, 'little'))
    for u in data:
        file.write(u['unit_id'].to_bytes(2, 'little'))
        file.write(u['shadow_id'].to_bytes(2, 'little'))
        flag_value = 0
        for f in u['flags']:
            flag_value += unit_flag_lookups[f]
        file.write(flag_value.to_bytes(4, 'little'))
        file.write(u['troop_transport'].to_bytes(1, 'little'))
        file.write(u['icon_id'].to_bytes(4, 'little'))
        file.write(len(u['name']).to_bytes(1, 'little'))
        file.write(u['name'].encode('ascii'))
        file.write(u['move'].to_bytes(1, 'little'))
        file.write(u['save'].to_bytes(1, 'little'))
        file.write(u['caf'].to_bytes(1, 'little'))
        for a in u['armour']:
            file.write(int(0).to_bytes(1, 'little'))
            file.write(a[0].to_bytes(1, 'little'))
            file.write(a[1].to_bytes(1, 'little'))
            file.write(a[2].to_bytes(1, 'little'))
            file.write(a[3].to_bytes(1, 'little'))
            file.write(a[4][0].to_bytes(2, 'little', signed=True))
            file.write(a[4][1].to_bytes(2, 'little', signed=True))
            file.write(a[4][2].to_bytes(2, 'little', signed=True))
        file.write(Chassis[u['chassis_type'].split('.')[1]].to_bytes(1, 'little'))
        file.write(len(u['weapons']).to_bytes(1, 'little'))
        file.write(Shields[u['shield_type'].split('.')[1]].to_bytes(1, 'little'))
        file.write(u['shields'].to_bytes(1, 'little'))
        file.write(u['hit_points'].to_bytes(1, 'little'))
        file.write(u['unit_cost'].to_bytes(2, 'little'))
        for i in range(8):
            file.write(footprint_from_int(u['footprint'][i]).to_bytes(1, 'little'))
        file.write(u['crit_damage'].to_bytes(1, 'little', signed=True))
        file.write(u['crit_pos'][0].to_bytes(1, 'little', signed=True))
        file.write(u['crit_pos'][1].to_bytes(1, 'little', signed=True))
        file.write(u['crit_pos'][2].to_bytes(1, 'little', signed=True))
        for i in range(11):  # even units with crits have bytes here
            file.write(Criticals[u['crits'][i][0].split('.')[1]].to_bytes(1, 'little', signed=True))
            file.write(Severity[u['crits'][i][1].split('.')[1]].to_bytes(1, 'little', signed=True))
            file.write(u['crits'][i][2].to_bytes(1, 'little', signed=True))
            file.write(u['crits'][i][3].to_bytes(1, 'little', signed=True))
        for w in u['weapons']:
            file.write(w['weapon_id'].to_bytes(2, 'little', signed=True))
        for w in u['weapons']:
            file.write(w['weapon_count'].to_bytes(1, 'little'))
        for w in u['weapons']:
            file.write(w['base_hit_chance'].to_bytes(1, 'little'))
        for w in u['weapons']:
            for i in range(3):
                file.write(w['offset'][i].to_bytes(1, 'little', signed=True))
            file.write(int(0).to_bytes(1, 'little', signed=True))
        file.write(u['start_of_secondary'].to_bytes(2, 'little'))
        file.write(u['start_of_missile'].to_bytes(2, 'little'))
        file.write(u['start_of_special'].to_bytes(2, 'little'))
