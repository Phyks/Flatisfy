<template lang="html">
    <div class="full">
        <v-map :zoom="zoom.defaultZoom" :center="center" :bounds="bounds" :min-zoom="zoom.minZoom" :max-zoom="zoom.maxZoom">
            <v-tilelayer :url="tiles.url" :attribution="tiles.attribution"></v-tilelayer>
            <template v-for="marker in flats">
                <v-marker :lat-lng="{ lat: marker.gps[0], lng: marker.gps[1] }" :icon="icons.flat">
                    <v-popup :content="marker.content"></v-popup>
                </v-marker>
            </template>
            <template v-for="(place_gps, place_name) in places">
                <v-marker :lat-lng="{ lat: place_gps[0], lng: place_gps[1] }" :icon="icons.place">
                    <v-tooltip :content="place_name"></v-tooltip>
                </v-marker>
            </template>
            <template v-for="journey in journeys">
                <v-geojson-layer :geojson="journey.geojson" :options="Object.assign({}, defaultGeoJSONOptions, journey.options)"></v-geojson-layer>
            </template>
        </v-map>
    </div>
</template>

<script>
import L from 'leaflet'
// Fix for a bug in Leaflet default icon
// see https://github.com/PaulLeCam/react-leaflet/issues/255#issuecomment-261904061
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

import 'leaflet/dist/leaflet.css'

require('leaflet.icon.glyph')

import Vue2Leaflet from 'vue2-leaflet'

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
            center: null,
            zoom: {
                defaultZoom: 13,
                minZoom: 11,
                maxZoom: 17
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
        'v-map': Vue2Leaflet.Map,
        'v-tilelayer': Vue2Leaflet.TileLayer,
        'v-marker': Vue2Leaflet.Marker,
        'v-tooltip': Vue2Leaflet.Tooltip,
        'v-popup': Vue2Leaflet.Popup,
        'v-geojson-layer': Vue2Leaflet.GeoJSON
    },

    computed: {
        bounds () {
            let bounds = []
            this.flats.forEach(flat => bounds.push(flat.gps))
            Object.keys(this.places).forEach(place => bounds.push(this.places[place]))

            if (bounds.length > 0) {
                bounds = L.latLngBounds(bounds)
                return bounds
            } else {
                return null
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
