import moment from 'moment'

require('es6-promise').polyfill()
require('isomorphic-fetch')

export const getFlats = function (callback) {
    fetch('/api/v1/flats', { credentials: 'same-origin' })
    .then(function (response) {
        return response.json()
    }).then(function (json) {
        const flats = json.data
        flats.map(flat => {
            if (flat.date) {
                flat.date = moment(flat.date)
            }
            return flat
        })
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
        const flat = json.data
        if (flat.date) {
            flat.date = moment(flat.date)
        }
        callback(json.data)
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
    ).then(callback)
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
