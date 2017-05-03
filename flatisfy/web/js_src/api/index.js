import moment from 'moment'

require('es6-promise').polyfill()
require('isomorphic-fetch')

const postProcessAPIResults = function (flat) {
    /* eslint-disable camelcase */
    if (flat.date) {
        flat.date = moment(flat.date)
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
        '/api/v1/flat/' + encodeURIComponent(flatId),
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
        '/api/v1/flat/' + encodeURIComponent(flatId) + '/status',
        {
            credentials: 'same-origin',
            method: 'POST',
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
        '/api/v1/flat/' + encodeURIComponent(flatId) + '/notes',
        {
            credentials: 'same-origin',
            method: 'POST',
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
        '/api/v1/flat/' + encodeURIComponent(flatId) + '/notation',
        {
            credentials: 'same-origin',
            method: 'POST',
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

export const getTimeToPlaces = function (callback) {
    fetch('/api/v1/time_to/places', { credentials: 'same-origin' })
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
