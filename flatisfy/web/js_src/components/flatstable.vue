<template lang="html">
    <table>
        <thead>
            <tr>
                <th v-if="showNotationColumn" class="pointer" v-on:click="updateSortBy('notation')">
                    {{ $t("flatsDetails.Notation") }}
                    <span v-if="sortBy === 'notation'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only">{{ $t("common.sort" + capitalize(sortOrder)) }}</span>
                    </span>
                </th>
                <th class="pointer" v-on:click="updateSortBy('title')">
                    {{ $t("flatsDetails.Title") }}
                    <span v-if="sortBy === 'title'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only">{{ $t("common.sort" + capitalize(sortOrder)) }}</span>
                    </span>
                </th>
                <th class="pointer" v-on:click="updateSortBy('area')">
                    {{ $t("flatsDetails.Area") }}
                    <span v-if="sortBy === 'area'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only">{{ $t("common.sort" + capitalize(sortOrder)) }}</span>
                    </span>
                </th>
                <th class="pointer" v-on:click="updateSortBy('rooms')">
                    {{ $t("flatsDetails.Rooms") }}
                    <span v-if="sortBy === 'rooms'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only">{{ $t("common.sort" + capitalize(sortOrder)) }}</span>
                    </span>
                </th>
                <th class="pointer" v-on:click="updateSortBy('cost')">
                    {{ $t("flatsDetails.Cost") }}
                    <span v-if="sortBy === 'cost'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only">{{ $t("common.sort" + capitalize(sortOrder)) }}</span>
                    </span>
                </th>
                <th class="pointer" v-on:click="updateSortBy('sqCost')">
                    {{ $t("flatsDetails.SquareMeterCost") }}
                    <span v-if="sortBy === 'sqCost'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only">{{ $t("common.sort" + capitalize(sortOrder)) }}</span>
                    </span>
                </th>
                <th>{{ $t("common.Actions") }}</th>
            </tr>
        </thead>
        <tbody>
            <FlatsTableLine :flat="flat" :showNotationColumn="showNotationColumn" :showNotes="showNotes" v-for="flat in sortedFlats" :key="flat.id"></FlatsTableLine>
        </tbody>
    </table>
</template>

<script>
import 'font-awesome-webpack'

import FlatsTableLine from './flatstableline.vue'

import { capitalize } from '../tools'

export default {
    components: {
        FlatsTableLine
    },

    data () {
        return {
            sortBy: this.initialSortBy,
            sortOrder: this.initialSortOrder
        }
    },

    props: {
        flats: Array,
        showNotationColumn: {
            type: Boolean,
            default: false
        },
        showNotes: {
            type: Boolean,
            default: false
        },
        initialSortBy: {
            type: String,
            default: 'cost'
        },
        initialSortOrder: {
            type: String,
            default: 'up'
        }
    },

    watch: {
        initialSortBy () {
            this.sortBy = this.initialSortBy
        },
        initialSortOrder () {
            this.sortOrder = this.initialSortOrder
        }
    },

    computed: {
        sortedFlats () {
            const sortedFlats = this.flats.slice(0)
            sortedFlats.sort(
                (flat1, flat2) => {
                    if (this.sortOrder === 'up') {
                        return flat1[this.sortBy] - flat2[this.sortBy]
                    } else {
                        return flat2[this.sortBy] - flat1[this.sortBy]
                    }
                }
            )
            return sortedFlats
        }
    },

    methods: {
        updateSortBy (field) {
            if (this.sortBy === field) {
                if (this.sortOrder === 'up') {
                    this.sortOrder = 'down'
                } else {
                    this.sortOrder = 'up'
                }
            } else {
                this.sortBy = field
            }
        },
        capitalize: capitalize
    }
}
</script>

<style scoped>
td a {
    display: inline-block;
    padding-left: 5px;
    padding-right: 5px;
    color: inherit;
}

td img {
    max-height: 100px;
}

button {
    border: none;
    background: transparent;
    font-size: 1em;
    cursor: pointer;
}

.pointer {
    cursor: pointer;
}

.sr-only {
    position:absolute;
    left:-10000px;
    top:auto;
    width:1px;
    height:1px;
    overflow:hidden;
}

pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    word-break: break-all;
}

.no-padding {
    padding: 0;
}

.fill {
    display: block;
    padding: 2em;
    text-decoration: none;
}
</style>
