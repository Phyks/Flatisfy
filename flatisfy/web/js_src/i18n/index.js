import Vue from 'vue'
import VueI18n from 'vue-i18n'
import moment from 'moment'

// Import translations
import en from './en'
import fr from './fr'

Vue.use(VueI18n)

export function getBrowserLocales () {
    let langs = []

    if (navigator.languages) {
        // Chrome does not currently set navigator.language correctly
        // https://code.google.com/p/chromium/issues/detail?id=101138
        // but it does set the first element of navigator.languages correctly
        langs = navigator.languages
    } else if (navigator.userLanguage) {
        // IE only
        langs = [navigator.userLanguage]
    } else {
        // as of this writing the latest version of firefox + safari set this correctly
        langs = [navigator.language]
    }

    // Some browsers does not return uppercase for second part
    const locales = langs.map(function (lang) {
        const locale = lang.split('-')
        return locale[1] ? `${locale[0]}-${locale[1].toUpperCase()}` : lang
    })

    return locales
}

const messages = {
    'en': en,
    'fr': fr
}

const locales = getBrowserLocales()

var locale = 'en'  // Safe default
// Get best matching locale
for (var i = 0; i < locales.length; ++i) {
    if (messages[locales[i]]) {
        locale = locales[i]
        break  // Break at first matching locale
    }
}

// Set the locale for Moment.js
moment.locale(locale)

export default new VueI18n({
    locale: locale,
    messages
})
