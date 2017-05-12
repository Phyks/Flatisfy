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
                <th>{{ $t("common.Actions") }}</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="flat in sortedFlats" :key="flat.id" v-on:click="event => showMore(event, flat.id)" class="pointer">
                <td v-if="showNotationColumn">
                    <template v-for="n in range(flat.notation)">
                        <i class="fa fa-star" aria-hidden="true" :title="capitalize($t('status.followed'))"></i>
                    </template>
                </td>
                <td>
                    <template v-if="!showNotationColumn" v-for="n in range(flat.notation)">
                        <i class="fa fa-star" aria-hidden="true" :title="capitalize($t('status.followed'))"></i>
                    </template>

                    [{{ flat.id.split("@")[1] }}] {{ flat.title }}

                    <template v-if="flat.photos && flat.photos.length > 0">
                        <br/>
                        <img :src="flat.photos[0].url"/>
                    </template>

                    <template v-if="showNotes">
                        <br/>
                        <pre>{{ flat.notes }}</pre>
                    </template>
                </td>
                <td>{{ flat.area }} m²</td>
                <td>
                    {{ flat.rooms ? flat.rooms : '?'}}
                    <span class="mobile-only">{{ $t("flatsDetails.RM") }}</span>
                </td>
                <td>
                    {{ flat.cost }} {{ flat.currency }}
                    <template v-if="flat.utilities == 'included'">
                        {{ $t("flatsDetails.utilities_included") }}
                    </template>
                    <template v-else-if="flat.utilities == 'excluded'">
                        {{ $t("flatsDetails.utilities_excluded") }}
                    </template>
                </td>
                <td>
                    <router-link :to="{name: 'details', params: {id: flat.id}}" :aria-label="$t('common.More_about') + ' ' + flat.id" :title="$t('common.More_about') + ' ' + flat.id">
                        <i class="fa fa-plus" aria-hidden="true"></i>
                    </router-link>
                    <a :href="flat.urls[0]" :aria-label="$t('common.Original_post_for') + ' ' + flat.id" :title="$t('common.Original_post_for') + ' ' + flat.id" target="_blank">
                        <i class="fa fa-external-link" aria-hidden="true"></i>
                    </a>
                    <button v-if="flat.status !== 'user_deleted'" v-on:click="updateFlatStatus(flat.id, 'user_deleted')" :aria-label="$t('common.Remove') + ' ' + flat.id" :title="$t('common.Remove') + ' ' + flat.id">
                        <i class="fa fa-trash" aria-hidden="true"></i>
                    </button>
                    <button v-else v-on:click="updateFlatStatus(flat.id, 'new')" :aria-label="$t('common.Restore') + ' ' + flat.id" :title="$t('common.Restore') + ' ' + flat.id">
                        <i class="fa fa-undo" aria-hidden="true"></i>
                    </button>
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script>
// TODO: Table is too wide on mobile device, and button trash is not aligned with links
import 'font-awesome-webpack'

import { capitalize, range } from '../tools'

export default {
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
        updateFlatStatus (id, status) {
            this.$store.dispatch('updateFlatStatus', { flatId: id, newStatus: status })
        },
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
        showMore (event, flatId) {
            if (event.target.tagName === 'TD') {
                this.$router.push({ name: 'details', params: { id: flatId }})
            }
        },
        capitalize: capitalize,
        range: range
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

@media screen and (max-width: 767px) {
    table {
        margin: 0;
        width: 100%;
    }

    thead {
        display: none;
    }

    th, td {
        padding: 0.25em;
    }

    td a, td button {
        display: block;
        width: 1em;
    }

    td {
        vertical-align: top;
    }
}
</style>
