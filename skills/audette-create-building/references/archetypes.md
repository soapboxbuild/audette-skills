# Audette Building Archetypes

Use this reference to map a property type to the correct Audette `building_archetype` value.

## Archetype Mapping

| Audette Archetype | Use When |
|-------------------|----------|
| `multi_unit_residential` | Apartment buildings, condominiums, co-ops, mixed-income housing, Section 8 / HUD / affordable housing, senior housing apartments (non-licensed care) |
| `townhomes` | Townhouse communities, row houses, attached single-family units |
| `longterm_care` | Licensed senior care facilities, assisted living, memory care, nursing homes, skilled nursing facilities |
| `office` | Office buildings, professional services, co-working spaces |
| `medical_office` | Medical office buildings, clinics, outpatient facilities (not hospitals) |
| `hotel` | Hotels, motels, extended stay, hospitality |
| `school` | K–12 schools, universities, community colleges, daycares |
| `food_retail_grocery` | Grocery stores, supermarkets, food halls |
| `non_food_retail_closed` | Enclosed retail stores, department stores, big box stores |
| `non_food_retail_open` | Strip malls, open-air shopping centers, retail plazas |
| `enclosed_mall` | Fully enclosed shopping malls |
| `quick_service_restaurant` | Fast food, fast casual, coffee shops, food courts |
| `full_service_restaurant` | Sit-down restaurants, bars, full-service dining |
| `recreation_complex` | Gyms, fitness centers, sports facilities, community centers |
| `warehouse` | Distribution centers, storage facilities, industrial buildings |

## Common Ambiguities

**Senior Housing**: Use `multi_unit_residential` for independent living apartment communities.
Use `longterm_care` only if the facility provides licensed care services (assisted living,
memory care, skilled nursing).

**Mixed-Use**: Choose based on the dominant use by floor area. If unsure, ask the user.

**Affordable / Section 8 / HUD**: These are `multi_unit_residential` regardless of subsidy type.

**HAP / LIHTC / RAD**: All map to `multi_unit_residential` unless the property is a licensed
care facility.

**Townhomes vs. Multi-Unit**: If units share walls but have individual entrances and multiple
floors per unit (townhouse style), use `townhomes`. For units with shared corridors and
single-floor layouts, use `multi_unit_residential`.
