<template lang="html">
    <div class="full">
        <v-map v-if="bounds" :zoom="zoom.defaultZoom" :bounds="bounds" :min-zoom="zoom.minZoom" :max-zoom="zoom.maxZoom" v-on:click="$emit('select-flat', null)" @update:bounds="bounds = $event">
            <v-tilelayer :url="tiles.url" :attribution="tiles.attribution"></v-tilelayer>
            <v-marker-cluster>
                <template v-for="marker in flats">
                        <v-marker :lat-lng="{ lat: marker.gps[0], lng: marker.gps[1] }" :icon="icons.flat" v-on:click="$emit('select-flat', marker.flatId)">
                            <!-- <v-popup :content="marker.content"></v-popup> -->
                        </v-marker>
                </template>
            </v-marker-cluster>
            <v-marker-cluster>
                <template v-for="(place_gps, place_name) in places">
                        <v-marker :lat-lng="{ lat: place_gps[0], lng: place_gps[1] }" :icon="icons.place">
                            <v-tooltip :content="place_name"></v-tooltip>
                        </v-marker>
                </template>
            </v-marker-cluster>
            <template v-for="journey in journeys">
                <v-geojson-layer :geojson="journey.geojson" :options="Object.assign({}, defaultGeoJSONOptions, journey.options)"></v-geojson-layer>
            </template>
        </v-map>
        <div v-else>Nothing to display yet</div>
    </div>
</template>

<script>
import L from 'leaflet'
// Fix for a bug in Leaflet default icon
// see https://github.com/PaulLeCam/react-leaflet/issues/255#issuecomment-261904061
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png')
})

import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

require('leaflet.icon.glyph')

import { LMap, LTileLayer, LMarker, LTooltip, LPopup, LGeoJson } from 'vue2-leaflet'
import Vue2LeafletMarkerCluster from 'vue2-leaflet-markercluster'

export default {
    data () {
        return {
            defaultGeoJSONOptions: {
                weight: 5,
                color: '#000',
                opacity: 1,
                fillColor: '#e4ce7f',
                fillOpacity: 1
            },
            bounds: [[40.91351257612758, -7.580566406250001], [51.65892664880053, 12.0849609375]],
            zoom: {
                defaultZoom: 6,
                minZoom: 5,
                maxZoom: 20
            },
            tiles: {
                url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
            },
            icons: {
                flat: new L.Icon.Default(),
                place: L.icon.glyph({
                    prefix: 'fa',
                    glyph: 'clock-o'
                })
            }
        }
    },

    components: {
        'v-map': LMap,
        'v-tilelayer': LTileLayer,
        'v-marker': LMarker,
        'v-marker-cluster': Vue2LeafletMarkerCluster,
        'v-tooltip': LTooltip,
        'v-popup': LPopup,
        'v-geojson-layer': LGeoJson
    },

    watch: {
        flats: 'computeBounds',
        places: 'computeBounds'
    },

    methods: {
        computeBounds (newData, oldData) {
            if (this.flats.length && JSON.stringify(newData) !== JSON.stringify(oldData)) {
                const allBounds = []
                this.flats.forEach(flat => allBounds.push(flat.gps))
                Object.keys(this.places).forEach(place => allBounds.push(this.places[place]))
                this.bounds = allBounds.length ? L.latLngBounds(allBounds) : undefined
            }
        }
    },

    props: ['flats', 'places', 'journeys']

    // TODO: Add a switch to display a layer with isochrones
}
</script>

<style lang="css">
.leaflet-popup-content {
    max-height: 20vh;
    overflow-y: auto;
}
</style>

<style lang="css" scoped>
.full {
    width: 100%;
    height: 75vh;
    background-color: #ddd;
}

#map {
    height: 100%;
}
</style>
