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
                    const previousMarkerIndex = markers.findIndex(
                        marker => marker.gps[0] === gps[0] && marker.gps[1] === gps[1]
                    )

                    const href = router.resolve({ name: 'details', params: { id: flat.id }}).href
                    if (previousMarkerIndex !== -1) {
                        markers[previousMarkerIndex].content += '<br/><a href="' + href + '">' + flat.title + '</a>'
                    } else {
                        markers.push({
                            'title': '',
                            'content': '<a href="' + href + '">' + flat.title + '</a>',
                            'gps': gps
                        })
                    }
                }
            }
        })

        return markers
    },

    allTimeToPlaces: state => state.timeToPlaces
}
