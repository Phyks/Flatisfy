<template>
    <div>
        <h1><router-link :to="{name: 'home'}">Flatisfy</router-link></h1>
        <nav>
            <ul>
                <li><router-link :to="{name: 'home'}">{{ $t("menu.available_flats") }}</router-link></li>
                <li><router-link :to="{name: 'status', params: {status: 'followed'}}">{{ $t("menu.followed_flats") }}</router-link></li>
                <li><router-link :to="{name: 'status', params: {status: 'new'}}">{{ $t("menu.by_status") }}</router-link></li>
                <li><router-link :to="{name: 'search' }">{{ $t("menu.search") }}</router-link></li>
            </ul>
        </nav>
        <router-view></router-view>
    </div>
</template>

<style>
body {
  margin: 0 auto;
  max-width: 75em;
  font-family: "Helvetica", "Arial", sans-serif;
  line-height: 1.5;
  padding: 4em 1em;
  padding-top: 1em;
  color: #555;
}

h1 {
    text-align: center;
}

h1,
h2,
strong,
th {
  color: #333;
}

table {
    border-collapse: collapse;
    margin: 1em;
    width: calc(100% - 2em);
    text-align: center;
}

th, td {
    padding: 1em;
    border: 1px solid black;
}

tbody>tr:hover {
    background-color: #DDD;
}
</style>

<style scoped>
h1 a {
    color: inherit;
    text-decoration: none;
}

nav {
    text-align: center;
}

nav ul {
    list-style-position: inside;
    padding: 0;
}

nav ul li {
    list-style: none;
    display: inline-block;
    padding-left: 1em;
    padding-right: 1em;
}
</style>
