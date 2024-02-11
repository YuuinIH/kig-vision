<script setup>
import jsmpeg from "jsmpeg";
import { onMounted } from "vue";

let canvas = null;
let player = null;
let ctx = null;
let client = null;
let host = import.meta.env.VITE_WS_HOST ? import.meta.env.VITE_WS_HOST : window.location.hostname;

onMounted(() => {
	console.log("init");
  client = new WebSocket("ws://" + host + "/ws");
  //heart beat
  client.onopen = function () {
    console.log("WS open");
    setInterval(() => {
      client.send("ping");
    }, 30000);
  };

  client.onerror = function (e) {
    console.log("WS error", e);
  };
  client.onclose = function () {
    console.log("WS closed");
  };
  canvas = document.getElementById("videoCanvas");

  ctx = canvas.getContext("2d");
  player = new jsmpeg(client, { canvas: canvas });
});
</script>

<template>
  <canvas id="videoCanvas" width="300" height="300">
    <p>
      Please use a browser that supports the Canvas Element, like
      <a href="http://www.google.com/chrome">Chrome</a>,
      <a href="http://www.mozilla.com/firefox/">Firefox</a>,
      <a href="http://www.apple.com/safari/">Safari</a> or Internet Explorer 10
    </p>
  </canvas>
</template>

<style>
#videoCanvas {
  width: 100%;
  height: 100%;
}
</style>
