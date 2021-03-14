<template>
<div>
    <template v-if="isLoading">
        <p>{{ $t("common.loading") }}</p>
    </template>
    <div class="grid" v-else-if="flat && timeToPlaces">
        <div class="left-panel">
            <h2>
                (<!--
                    --><router-link :to="{ name: 'status', params: { status: flat.status }}"><!--
                        -->{{ flat.status ? capitalize($t("status." + flat.status)) : '' }}<!--
                    --></router-link><!--
                -->) {{ flat.title }} [{{ flat.id.split("@")[1] }}]
                <span class="expired">{{ flat.is_expired ? '[' + $t('common.expired') + ']' : '' }}</span>
            </h2>
            <div class="grid">
                <div class="left-panel">
                    <span>
                        {{ flat.cost | cost(flat.currency) }}
                        <template v-if="flat.utilities === 'included'">
                            {{ $t("flatsDetails.utilities_included") }}
                        </template>
                        <template v-else-if="flat.utilities === 'excluded'">
                            {{ $t("flatsDetails.utilities_excluded") }}
                        </template>
                    </span>
                    <span v-if="flat.flatisfy_postal_code.postal_code">
                        à {{ flat.flatisfy_postal_code.name }} ({{ flat.flatisfy_postal_code.postal_code }})
                    </span>
                </div>
                <span class="right-panel right">
                    <template v-if="flat.area"><span>{{flat.area}} m<sup>2</sup></span></template><template v-if="flat.rooms"><span>, {{flat.rooms}} {{ $tc("flatsDetails.rooms", flat.rooms) }}</span></template><template v-if="flat.bedrooms"><span>/ {{flat.bedrooms}} {{ $tc("flatsDetails.bedrooms", flat.bedrooms) }}</span></template>
                </span>
            </div>
            <div>
                <template v-if="flat.photos && flat.photos.length > 0">
                    <Slider :photos="flat.photos"></Slider>
                </template>
            </div>
            <div>
                <h3>{{ $t("flatsDetails.Description") }}</h3>
                <p>{{ flat.text }}</p>
                <p class="right">{{ flat.location }}</p>
                <p>{{ $t("flatsDetails.First_posted") }} {{ flat.date ? flat.date.fromNow() : '?' }}.</p>
            </div>
            <div>
                <h3>{{ $t("flatsDetails.Details") }}</h3>
                <table>
                    <tr v-for="(value, key) in flat.details">
                        <th>{{ key }}</th>
                        <td>{{ value }}</td>
                    </tr>
                </table>
            </div>
            <div>
                <h3>{{ $t("flatsDetails.Metadata") }}</h3>
                <table>
                    <tr>
                        <th>
                            {{ $t("flatsDetails.postal_code") }}
                        </th>
                        <td>
                            <template v-if="flat.flatisfy_postal_code.postal_code">
                                {{ flat.flatisfy_postal_code.name }} ({{ flat.flatisfy_postal_code.postal_code }})
                            </template>
                            <template v-else>
                                ?
                            </template>
                        </td>
                    </tr>

                    <tr v-if="displayedStations">
                        <th>
                            {{ $t("flatsDetails.nearby_stations") }}
                        </th>
                        <td>
                            {{ displayedStations }}
                        </td>
                    </tr>
                    <tr v-if="Object.keys(flat.flatisfy_time_to).length">
                        <th>
                            {{ $t("flatsDetails.Times_to") }}
                        </th>
                        <td>
                            <ul class="time_to_list">
                                <li v-for="(time_to, place) in flat.flatisfy_time_to" :key="place">
                                    {{ place }}: {{ humanizeTimeTo(time_to["time"]) }}
                                </li>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <th>
                            {{ $t("flatsDetails.SquareMeterCost") }}
                        </th>
                        <td>
                            {{ flat.sqCost }} {{ flat.currency }}
                        </td>
                    </tr>
                </table>
            </div>
            <div>
                <h3>{{ $t("flatsDetails.Location") }}</h3>

                <FlatsMap :flats="flatMarker" :places="timeToPlaces" :journeys="journeys"></FlatsMap>
            </div>
            <div>
                <h3>{{ $t("flatsDetails.Notes") }}</h3>

                <form v-on:submit="updateFlatNotes">
                    <textarea ref="notesTextarea" rows="10" :v-model="flat.notes"></textarea>
                    <p class="right"><input type="submit" :value="$t('flatsDetails.Save')"/></p>
                </form>
            </div>
        </div>

        <div class="right-panel">
            <h3>{{ $t("flatsDetails.Contact") }}</h3>
            <div class="contact">
                <template v-if="flat.phone">
                    <p v-for="phoneNumber in flat.phone.split(',')">
                        <a :href="'tel:+33' + normalizePhoneNumber(phoneNumber)">{{ phoneNumber }}</a>
                    </p>
                </template>
                <template v-if="flat.urls.length == 1">
                    <a :href="flat.urls[0]" target="_blank">
                        {{ $tc("common.Original_post", 1) }}
                        <i class="fa fa-external-link" aria-hidden="true"></i>
                    </a>
                </template>
                <template v-else-if="flat.urls.length > 1">
                    <p>{{ $tc("common.Original_post", flat.urls.length) }}
                        <ul>
                            <li v-for="(url, index) in flat.urls">
                                <a :href="url" target="_blank">
                                    {{ $tc("common.Original_post", 1) }} {{ index + 1 }}
                                    <i class="fa fa-external-link" aria-hidden="true"></i>
                                </a>
                            </li>
                        </ul>
                    </p>
                </template>
            </div>

            <h3>{{ $t("flatsDetails.Visit") }}</h3>
            <div class="visit">
                <flat-pickr
                    :value="flatpickrValue"
                    :config="flatpickrConfig"
                    :placeholder="$t('flatsDetails.setDateOfVisit')"
                />
            </div>

            <h3>{{ $t("common.Actions") }}</h3>

            <nav>
                <ul>
                    <template v-if="flat.status !== 'user_deleted'">
                        <Notation :flat="flat"></Notation>
                        <li>
                            <button v-on:click="updateFlatStatus('user_deleted')" class="fullButton">
                                <i class="fa fa-trash" aria-hidden="true"></i>
                                {{ $t("common.Remove") }}
                            </button>
                        </li>
                    </template>
                    <template v-else>
                        <li>
                            <button v-on:click="updateFlatStatus('new')" class="fullButton">
                                <i class="fa fa-undo" aria-hidden="true"></i>
                                {{ $t("common.Restore") }}
                            </button>
                        </li>
                    </template>
                </ul>
            </nav>
        </div>
    </div>
</div>
</template>

<script>
import flatPickr from 'vue-flatpickr-component'
import moment from 'moment'
import 'font-awesome-webpack'
import 'flatpickr/dist/flatpickr.css'

import FlatsMap from '../components/flatsmap.vue'
import Slider from '../components/slider.vue'
import Notation from '../components/notation.vue'

import { capitalize } from '../tools'

export default {
    components: {
        FlatsMap,
        Slider,
        flatPickr,
        Notation
    },

    created () {
        this.fetchData()
    },

    data () {
        return {
            // TODO: Flatpickr locale
            'overloadNotation': null,
            'flatpickrConfig': {
                static: true,
                altFormat: 'h:i K, M j, Y',
                altInput: true,
                enableTime: true,
                onChange: selectedDates => this.updateFlatVisitDate(selectedDates.length > 0 ? selectedDates[0] : null)
            }
        }
    },

    props: ['flat'],

    computed: {
        isLoading () {
            return this.$store.getters.isLoading
        },
        flatMarker () {
            return this.$store.getters.flatsMarkers(this.$router, flat => flat.id === this.flat.id)
        },
        'flatpickrValue' () {
            if (this.flat && this.flat.visit_date) {
                return this.flat.visit_date.local().format()
            }
            return null
        },
        timeToPlaces () {
            return this.$store.getters.timeToPlaces(this.flat.flatisfy_constraint)
        },
        notation () {
            if (this.overloadNotation) {
                return this.overloadNotation
            }
            return this.flat.notation
        },
        journeys () {
            if (Object.keys(this.flat.flatisfy_time_to).length > 0) {
                const journeys = []
                for (const place in this.flat.flatisfy_time_to) {
                    this.flat.flatisfy_time_to[place].sections.forEach(
                        section => journeys.push({
                            geojson: section.geojson,
                            options: {
                                color: section.color ? ('#' + section.color) : '#2196f3',
                                dashArray: section.color ? 'none' : '2, 10'
                            }
                        })
                    )
                }
                return journeys
            }
            return []
        },
        displayedStations () {
            if (this.flat.flatisfy_stations.length > 0) {
                const stationsNames = this.flat.flatisfy_stations.map(station => station.name)
                return stationsNames.join(', ')
            } else {
                return null
            }
        }
    },

    watch: {
        flat: 'fetchData'
    },

    methods: {
        fetchData () {
            this.$store.dispatch('getAllTimeToPlaces')
        },

        updateFlatStatus (status) {
            this.$store.dispatch('updateFlatStatus', { flatId: this.flat.id, newStatus: status })
        },

        updateFlatNotes () {
            const notes = this.$refs.notesTextarea.value
            this.$store.dispatch(
                'updateFlatNotes',
                { flatId: this.flat.id, newNotes: notes }
            )
        },

        updateFlatVisitDate (date) {
            if (date) {
                date = moment(date).utc().format()
            }
            this.$store.dispatch(
                'updateFlatVisitDate',
                { flatId: this.flat.id, newVisitDate: date }
            )
        },

        humanizeTimeTo (time) {
            const minutes = Math.floor(time.as('minutes'))
            return minutes + ' ' + this.$tc('common.mins', minutes)
        },

        normalizePhoneNumber (phoneNumber) {
            phoneNumber = phoneNumber.replace(/ /g, '')
            phoneNumber = phoneNumber.replace(/\./g, '')
            return phoneNumber
        },

        capitalize: capitalize
    }
}
</script>

<style scoped>
.expired {
    font-weight: bold;
    text-transform: uppercase;
}

@media screen and (min-width: 768px) {
    .grid {
        display: grid;
        grid-gap: 50px;
        grid-template-columns: 75fr 25fr;
    }

    .left-panel {
        grid-column: 1;
        grid-row: 1;
    }

    .right-panel {
        grid-column: 2;
        grid-row: 1;
    }
}

.left-panel textarea {
    width: 100%;
}

.right {
    text-align: right;
}

nav ul {
    list-style-type: none;
    padding-left: 1em;
}

.contact {
    padding-left: 1em;
}

.right-panel li {
    margin-bottom: 1em;
    margin-top: 1em;
}

button {
    cursor: pointer;
    width: 75%;
    padding: 0.3em;
    font-size: 0.9em;
}

table {
    table-layout: fixed;
}

td {
    word-wrap: break-word;
    word-break: break-all;
    white-space: normal;
}

.time_to_list {
    margin: 0;
    padding-left: 0;
    list-style-position: outside;
    list-style-type: none;
}

@media screen and (max-width: 767px) {
    .right-panel nav {
        text-align: center;
    }

    .fullButton {
        width: 100%;
    }
}
</style>
