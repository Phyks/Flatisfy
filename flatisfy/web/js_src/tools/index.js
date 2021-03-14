export function findFlatGPS (flat) {
    let gps

    if (flat.flatisfy_position) {
        gps = [flat.flatisfy_position.lat, flat.flatisfy_position.lng]
    } else if (flat.flatisfy_stations && flat.flatisfy_stations.length > 0) {
        // Try to push a marker based on stations
        gps = [0.0, 0.0]
        flat.flatisfy_stations.forEach(station => {
            gps = [gps[0] + station.gps[0], gps[1] + station.gps[1]]
        })
        gps = [gps[0] / flat.flatisfy_stations.length, gps[1] / flat.flatisfy_stations.length]
    } else {
        // Else, push a marker based on postal code
        gps = flat.flatisfy_postal_code.gps
    }

    return gps
}

export function capitalize (string) {
    return string.charAt(0).toUpperCase() + string.slice(1)
}

export function range (n) {
    return [...Array(n).keys()]
}

export function costFilter (value, currency) {
    if (!value) {
        return 'N/A'
    }

    if (currency === 'EUR') {
        currency = ' €'
    }

    var valueStr = value.toString()
    valueStr = ' '.repeat((3 + valueStr.length) % 3) + valueStr

    return valueStr.match(/.{1,3}/g).join('.') + currency
}
