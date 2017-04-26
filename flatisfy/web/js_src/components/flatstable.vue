<template lang="html">
    <table>
        <thead>
            <tr>
                <th class="pointer" v-on:click="updateSortBy('title')">
                    {{ $t("flatsDetails.Title") }}
                    <span v-if="sortBy === 'title'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only"></span>
                    </span>
                </th>
                <th class="pointer" v-on:click="updateSortBy('area')">
                    {{ $t("flatsDetails.Area") }}
                    <span v-if="sortBy === 'area'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only"></span>
                    </span>
                </th>
                <th class="pointer" v-on:click="updateSortBy('rooms')">
                    {{ $t("flatsDetails.Rooms") }}
                    <span v-if="sortBy === 'rooms'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only"></span>
                    </span>
                </th>
                <th class="pointer" v-on:click="updateSortBy('cost')">
                    {{ $t("flatsDetails.Cost") }}
                    <span v-if="sortBy === 'cost'">
                        <i class="fa" :class="'fa-angle-' + sortOrder" aria-hidden="true"></i>
                        <span class="sr-only"></span>
                    </span>
                </th>
                <th>{{ $t("common.Actions") }}</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="flat in sortedFlats" :key="flat.id">
                <td>
                    [{{ flat.id.split("@")[1] }}] {{ flat.title }}

                    <template v-if="flat.photos && flat.photos.length > 0">
                        <br/>
                        <img :src="flat.photos[0].url"/>
                    </template>
                </td>
                <td>{{ flat.area }} m²</td>
                <td>
                    {{ flat.rooms ? flat.rooms : '?'}}
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
                    <router-link :to="{name: 'details', params: {id: flat.id}}" :aria-label="$t('common.More')" :title="$t('common.More')">
                        <i class="fa fa-plus" aria-hidden="true"></i>
                    </router-link>
                    <a :href="flat.urls[0]" :aria-label="$t('common.External_link')" :title="$t('common.External_link')" target="_blank">
                        <i class="fa fa-external-link" aria-hidden="true"></i>
                    </a>
                    <button v-if="flat.status !== 'user_deleted'" v-on:click="updateFlatStatus(flat.id, 'user_deleted')" :aria-label="$t('common.Remove')" :title="$t('common.Remove')">
                        <i class="fa fa-trash" aria-hidden="true"></i>
                    </button>
                    <button v-else v-on:click="updateFlatStatus(flat.id, 'new')" :aria-label="$t('common.Restore')" :title="$t('common.Restore')">
                        <i class="fa fa-undo" aria-hidden="true"></i>
                    </button>
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script>
import "font-awesome-webpack"

export default {
    data () {
        return {
            sortBy: 'cost',
            sortOrder: 'up'
        }
    },

    props: ['flats'],

    computed: {
        sortedFlats () {
            return this.flats.sort(
                (flat1, flat2) => {
                    if (this.sortOrder === "up") {
                        return flat1[this.sortBy] > flat2[this.sortBy]
                    } else {
                        return flat1[this.sortBy] < flat2[this.sortBy]
                    }
                }
            )
        }
    },

    methods: {
        updateFlatStatus (id, status) {
            this.$store.dispatch('updateFlatStatus', { flatId: id, newStatus: status })
        },
        updateSortBy (field) {
            if (this.sortBy === field) {
                if (this.sortOrder === "up") {
                    this.sortOrder = "down"
                } else {
                    this.sortOrder = "up"
                }
            } else {
                this.sortBy = field;
            }
        }
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
</style>
