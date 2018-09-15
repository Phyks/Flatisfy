<template>
    <tr>
        <td v-if="showNotationColumn">
            <template v-for="n in notationRange">
                <i class="fa fa-star" aria-hidden="true" :title="capitalizedStatus"></i>
            </template>
        </td>
        <td class="no-padding">
            <router-link class="fill" :to="{name: 'details', params: {id: flat.id}}">
                <template v-if="!showNotationColumn" v-for="n in notationRange">
                    <i class="fa fa-star" aria-hidden="true" :title="capitalizedStatus"></i>
                </template>

                [{{ flat.id.split("@")[1] }}] {{ flat.title }}

                <template v-if="photo">
                    <br/>
                    <img :src="photo" height="200" style="max-width: 25vw" />
                </template>

                <template v-if="showNotes">
                    <br/>
                    <pre>{{ flat.notes }}</pre>
                </template>
            </router-link>
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
            {{ flat.sqCost }} {{ flat.currency }}
        </td>
        <td>
            <router-link :to="{name: 'details', params: {id: flat.id}}" :aria-label="$t('common.More_about') + ' ' + flat.id" :title="$t('common.More_about') + ' ' + flat.id">
                <i class="fa fa-eye" aria-hidden="true"></i>
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
</template>

<script>
import { capitalize, range } from '../tools'

export default {
    props: {
        flat: Object,
        showNotationColumn: Boolean,
        showNotes: Boolean,
    },

    computed: {
        capitalizedStatus() {
            return capitalize(this.$t('status.followed'));
        },
        photo() {
            if (this.flat.photos && this.flat.photos.length > 0) {
                if (this.flat.photos[0].local) {
                    return `/data/img/${this.flat.photos[0].local}`;
                }
                return this.flat.photos[0].url;
            }
            return null;
        },
        notationRange() {
            return range(this.flat.notation);
        },
    },
};
</script>
