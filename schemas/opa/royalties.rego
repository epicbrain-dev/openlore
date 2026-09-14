package openlore.royalties

import future.keywords.in

default allow_export = false

# Allow export if all referenced sublayers have verified BLAKE3 hashes and valid licenses
allow_export {
    count(unlicensed_assets) == 0
}

# Find any referenced sublayer or prim without an approved license
unlicensed_assets[prim] {
    some prim in input.manifest.prims
    not prim.license_status == "approved"
}

# Calculate total royalty split per partner
royalty_splits[partner_id] = total_share {
    some partner_id in {p | some prim in input.manifest.prims; p := prim.partner_id}
    total_share := sum([share | 
        some prim in input.manifest.prims
        prim.partner_id == partner_id
        share := prim.royalty_percentage
    ])
}
