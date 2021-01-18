import { findFlatGPS } from '../tools'

export default {
    allFlats: state => state.flats,

    flat: (state, getters) => id => state.flats.find(flat => flat.id === id),

    isLoading: state => state.loading > 0,

    postalCodesFlatsBuckets: (state, getters) => filter => {
        const postalCodeBuckets = {}

        state.flats.forEach(flat => {
            if (!filter || filter(flat)) {
                const postalCode = flat.flatisfy_postal_code.postal_code
                if (!postalCodeBuckets[postalCode]) {
                    postalCodeBuckets[postalCode] = {
                        'name': flat.flatisfy_postal_code.name,
                        'flats': []
                    }
                }
                postalCodeBuckets[postalCode].flats.push(flat)
            }
        })

        return postalCodeBuckets
    },

    flatsMarkers: (state, getters) => (router, filter) => {
        const markers = []
        state.flats.forEach(flat => {
            if (filter && filter(flat)) {
                const gps = findFlatGPS(flat)

                if (gps) {
                    const previousMarker = markers.find(
                        marker => marker.gps[0] === gps[0] && marker.gps[1] === gps[1]
                    )
                    if (previousMarker) {
                        // randomize position a bit
                        // gps[0] += (Math.random() - 0.5) / 500
                        // gps[1] += (Math.random() - 0.5) / 500
                    }
                    const href = router.resolve({ name: 'details', params: { id: flat.id }}).href
                    const cost = flat.cost ? ' ( ' + flat.cost + '€)' : ''
                    markers.push({
                        'title': '',
                        'content': '<a href="' + href + '">' + flat.title + '</a>' + cost,
                        'gps': gps
                    })
                }
            }
        })

        return markers
    },

    allTimeToPlaces: state => {
        const places = {}
        Object.keys(state.timeToPlaces).forEach(constraint => {
            const constraintTimeToPlaces = state.timeToPlaces[constraint]
            Object.keys(constraintTimeToPlaces).forEach(name => {
                places[name] = constraintTimeToPlaces[name]
            })
        })
        return places
    },

    timeToPlaces: (state, getters) => (constraintName) => {
        return state.timeToPlaces[constraintName]
    },

    metadata: state => state.metadata
}
