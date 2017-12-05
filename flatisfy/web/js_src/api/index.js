import moment from 'moment'

require('es6-promise').polyfill()
require('isomorphic-fetch')

const postProcessAPIResults = function (flat) {
    /* eslint-disable camelcase */
    if (flat.date) {
        flat.date = moment.utc(flat.date)
    }
    if (flat.visit_date) {
        flat.visit_date = moment.utc(flat.visit_date)
    }
    if (flat.flatisfy_time_to) {
        const momentifiedTimeTo = {}
        Object.keys(flat.flatisfy_time_to).forEach(key => {
            const value = flat.flatisfy_time_to[key]
            momentifiedTimeTo[key] = Object.assign(
                {},
                value,
                { time: moment.duration(value.time, 'seconds') }
            )
        })
        flat.flatisfy_time_to = momentifiedTimeTo
    }

    // Fill cost per square meter.
    flat.sqCost = Math.round(flat.cost * 100 / flat.area) / 100 | 0

    /* eslint-enable camelcase */
    return flat
}

export const getFlats = function (callback) {
    fetch('/api/v1/flats', { credentials: 'same-origin' })
    .then(function (response) {
        return response.json()
    }).then(function (json) {
        const flats = json.data
        flats.map(postProcessAPIResults)
        callback(flats)
    }).catch(function (ex) {
        console.error('Unable to parse flats: ' + ex)
    })
}

export const getFlat = function (flatId, callback) {
    fetch(
        '/api/v1/flats/' + encodeURIComponent(flatId),
        { credentials: 'same-origin' }
    )
    .then(function (response) {
        return response.json()
    }).then(function (json) {
        const flat = postProcessAPIResults(json.data)
        callback(flat)
    }).catch(function (ex) {
        console.error('Unable to parse flats: ' + ex)
    })
}

export const updateFlatStatus = function (flatId, newStatus, callback) {
    fetch(
        '/api/v1/flats/' + encodeURIComponent(flatId),
        {
            credentials: 'same-origin',
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: newStatus
            })
        }
    ).then(callback).catch(function (ex) {
        console.error('Unable to update flat status: ' + ex)
    })
}

export const updateFlatNotes = function (flatId, newNotes, callback) {
    fetch(
        '/api/v1/flats/' + encodeURIComponent(flatId),
        {
            credentials: 'same-origin',
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                notes: newNotes
            })
        }
    ).then(callback).catch(function (ex) {
        console.error('Unable to update flat notes: ' + ex)
    })
}

export const updateFlatNotation = function (flatId, newNotation, callback) {
    fetch(
        '/api/v1/flats/' + encodeURIComponent(flatId),
        {
            credentials: 'same-origin',
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                notation: newNotation
            })
        }
    ).then(callback).catch(function (ex) {
        console.error('Unable to update flat notation: ' + ex)
    })
}

export const updateFlatVisitDate = function (flatId, newVisitDate, callback) {
    fetch(
        '/api/v1/flats/' + encodeURIComponent(flatId),
        {
            credentials: 'same-origin',
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                visit_date: newVisitDate  // eslint-disable-line camelcase
            })
        }
    ).then(callback).catch(function (ex) {
        console.error('Unable to update flat date of visit: ' + ex)
    })
}

export const getTimeToPlaces = function (callback) {
    fetch('/api/v1/time_to_places', { credentials: 'same-origin' })
    .then(function (response) {
        return response.json()
    }).then(function (json) {
        callback(json.data)
    }).catch(function (ex) {
        console.error('Unable to fetch time to places: ' + ex)
    })
}

export const doSearch = function (query, callback) {
    fetch(
        '/api/v1/search',
        {
            credentials: 'same-origin',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query
            })
        }
    ).then(response => response.json()).then(json => {
        callback(json.data)
    }).catch(function (ex) {
        console.error('Unable to perform search: ' + ex)
    })
}
