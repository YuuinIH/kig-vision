<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";
import "element-plus/dist/index.css";
import stream from "./stream.vue";

const httpClient = axios.create();
if (import.meta.env.MODE === "development") {
  httpClient.defaults.baseURL = import.meta.env.VITE_HOST;
}

const baseURL = import.meta.env.VITE_HOST;

const activeName = ref("cameraConfig");
const resolutionOptions = ref([]);
const fpsOptions = ref([]);
const preViewResolutionOptions = ref([]);
const selectedResolution = ref("");
const selectedFPS = ref(0);
const selectedPreviewResolution = ref("");
const captureList = ref([]);
const multipleCaptureSelection = ref([]);
const recordList = ref([]);
const multipleRecordSelection = ref([]);
const nowhflip = ref(true);
const nowvflip = ref(true);
const isRecording = ref(false);
const showingVideo = ref(false);
const showingVideoSrc = ref("");
const modeOptions = ref(["record", "stream"]);
const mode = ref("record");

const getConfigOptions = async () => {
  const response = await httpClient.options("/config");
  const { resolution, fps, preViewResolution } = response.data;
  resolutionOptions.value = resolution.map((r) => r.join("x"));
  fpsOptions.value = fps;
  preViewResolutionOptions.value = preViewResolution.map((r) => r.join("x"));
};

const getConfig = async () => {
  const response = await httpClient.get("/config");
  const { resolution, fps, preViewResolution, hflip, vflip } = response.data;
  selectedResolution.value = resolution.join("x");
  selectedFPS.value = fps;
  selectedPreviewResolution.value = preViewResolution.join("x");
  nowhflip.value = hflip;
  nowvflip.value = vflip;
};

const updateConfig = async () => {
  const resolution = selectedResolution.value.split("x").map(Number);
  const preViewResolution = selectedPreviewResolution.value
    .split("x")
    .map(Number);
  await httpClient.post("/config", {
    resolution,
    fps: selectedFPS.value,
    preViewResolution,
    hflip: nowhflip.value,
    vflip: nowvflip.value,
  });
  ElMessage.success("Configuration updated");
};

const startPreview = async () => {
  await httpClient.post("/start");
  ElMessage.success("Preview started");
};

const stopPreview = async () => {
  await httpClient.post("/stop");
  ElMessage.success("Preview stopped");
};

const captureImage = async () => {
  await httpClient.post("/capture");
  getCaptureList();
  ElMessage.success("Image captured");
};

const handleCaptureSelectionChange = (val) => {
  multipleCaptureSelection.value = val;
  console.log(multipleCaptureSelection.value);
};

const getCaptureList = async () => {
  const response = await httpClient.get("/capture");
  captureList.value = response.data.capturelist;
};

const deleteCapture = async (name) => {
  await httpClient.delete(`/capture/${name}`);
  getCaptureList();
  ElMessage.success("Image deleted");
};

const deleteCaptures = async (name) => {
  await httpClient.post(`/deleteCaptures`, { filename: name });
  getCaptureList();
  ElMessage.success("Images deleted");
};

const recordVideo = async () => {
  await httpClient.post("/record");
  getRecordList();
  ElMessage.success("Recording started");
};

const stopRecordVideo = async () => {
  await httpClient.post("/stopRecord");
  getRecordList();
  ElMessage.success("Recording stopped");
};

const handleRecordSelectionChange = (val) => {
  multipleRecordSelection.value = val;
  console.log(multipleRecordSelection.value);
};

const getRecordList = async () => {
  const response = await httpClient.get("/record");
  recordList.value = response.data.recordlist;
  isRecording.value = response.data.status;
};

const deleteRecord = async (name) => {
  await httpClient.delete(`/record/${name}`);
  getRecordList();
  ElMessage.success("Video deleted");
};

const deleteRecords = async (name) => {
  await httpClient.post(`/deleteRecords`, { filename: name });
  getRecordList();
  ElMessage.success("Videos deleted");
};

const setmode = async (mode) => {
  await httpClient.post("/mode", { mode });
  ElMessage.success("Mode set");
  fresh();
};

const getmode = async () => {
  const response = await httpClient.get("/mode");
  mode.value = response.data.mode;
};

const fresh = async () => {
  getCaptureList();
  getRecordList();
  getmode();
  getConfig();
};

const freshStreamCount = ref(true);

const freshStream = async () => {
  freshStreamCount.value = false;
  setTimeout(() => {
    freshStreamCount.value = true;
  }, 50);
};

onMounted(() => {
  getConfigOptions();
  getConfig();
  getCaptureList();
  getRecordList();
  getmode();
  // initCanvas();
});
</script>

<template>
  <div>
    <el-row justify="center">
      <el-col :span="22">
        <el-tabs v-model="activeName">
          <el-button slot="nav" @click="fresh" text size="large">
            <el-icon><RefreshRight /></el-icon>
          </el-button>
          <el-tab-pane label="Camera Configuration" name="cameraConfig">
            <h2>Camera Configuration</h2>
            <el-form>
              <el-form-item label="Resolution">
                <el-select v-model="selectedResolution" @change="updateConfig">
                  <el-option
                    v-for="option in resolutionOptions"
                    :key="option"
                    :label="`${option}`"
                    :value="option"
                  ></el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="FPS">
                <el-select v-model="selectedFPS" @change="updateConfig">
                  <el-option
                    v-for="option in fpsOptions"
                    :key="option"
                    :label="option"
                    :value="option"
                  ></el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="Preview Resolution">
                <el-select
                  v-model="selectedPreviewResolution"
                  @change="updateConfig"
                >
                  <el-option
                    v-for="option in preViewResolutionOptions"
                    :key="option"
                    :label="`${option}`"
                    :value="option"
                  ></el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="HFlip">
                <el-switch v-model="nowhflip" @change="updateConfig"
                  >Enable</el-switch
                >
              </el-form-item>

              <el-form-item label="VFlip">
                <el-switch v-model="nowvflip" @change="updateConfig"
                  >Enable</el-switch
                >
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="startPreview"
                  >Start Preview</el-button
                >
                <el-button @click="stopPreview">Stop Preview</el-button>
              </el-form-item>
              <el-form-item>
                <el-button @click="captureImage">Capture Image</el-button>
              </el-form-item>
              <el-form-item>
                <p>Mode:</p>
                <el-radio-group v-model="mode" size="large" @change="setmode">
                  >
                  <el-radio-button
                    :label="option"
                    v-for="option in modeOptions"
                    :key="option"
                    >{{ option }}</el-radio-button
                  >
                </el-radio-group>
              </el-form-item>
              <el-form-item v-show="mode == 'record'">
                recording: {{ isRecording ? "Yes" : "No" }}
              </el-form-item>
              <el-form-item v-show="mode == 'record'">
                <el-button @click="recordVideo">Record Video</el-button>
                <el-button @click="stopRecordVideo">Stop Recording</el-button>
              </el-form-item>
              <el-form-item v-if="mode == 'stream'">
                <el-button @click="freshStream">Refresh</el-button>
                <stream v-if="freshStreamCount" />
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane name="imageCapture" label="Image Capture">
            <el-col>
              <h2>Image Capture</h2>
              <el-row
                ><el-button @click="captureImage"
                  >Capture Image</el-button
                ></el-row
              >
              <el-row
                ><el-button
                  type="danger"
                  @click="deleteCaptures(multipleCaptureSelection)"
                  >Delete Selected</el-button
                ></el-row
              >
              <el-table
                :data="captureList"
                @selection-change="handleCaptureSelectionChange"
              >
                <el-table-column type="selection" width="55" />
                <el-table-column label="Image">
                  <template #default="scope">
                    <el-image
                      style="width: 100px; height: 100px"
                      :src="baseURL + '/capture/' + captureList[scope.$index]"
                      :preview-src-list="
                        captureList.map(
                          (capture) => baseURL + '/capture/' + capture
                        )
                      "
                      :initial-index="scope.$index"
                      :z-index="9999"
                      :preview-teleported="true"
                      :hide-on-click-modal="true"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="Download">
                  <template #default="scope">
                    <el-button
                      link
                      tag="a"
                      type="primary"
                      :href="baseURL + '/capture/' + captureList[scope.$index]"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Download
                    </el-button>
                  </template>
                </el-table-column>
                <el-table-column label="Delete">
                  <template #default="scope">
                    <el-button
                      type="danger"
                      @click="deleteCapture(captureList[scope.$index])"
                      >Delete</el-button
                    >
                  </template>
                </el-table-column>
              </el-table>
            </el-col>
          </el-tab-pane>

          <el-tab-pane name="videorecording" label="Video Recording">
            <h2>Video Recording</h2>
            <el-row
              ><el-button @click="recordVideo" :disabled="mode != 'record'"
                >Record Video</el-button
              ><el-button @click="stopRecordVideo" :disabled="mode != 'record'"
                >Stop Recording</el-button
              ></el-row
            >
            <el-row
              ><el-button
                type="danger"
                @click="deleteRecords(multipleRecordSelection)"
                >Delete Selected</el-button
              ></el-row
            >
            <el-table
              :data="recordList"
              style="width: 100%"
              @selection-change="handleRecordSelectionChange"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column label="Viedo">
                <template #default="scope">
                  <el-button
                    link
                    tag="a"
                    @click="
                      (showingVideo = true),
                        (showingVideoSrc =
                          baseURL + '/record/' + recordList[scope.$index])
                    "
                    >{{ recordList[scope.$index] }}</el-button
                  >
                </template>
              </el-table-column>
              <el-table-column>
                <template #default="scope">
                  <el-button
                    link
                    tag="a"
                    type="primary"
                    :href="baseURL + '/record/' + recordList[scope.$index]"
                    target="_blank"
                    rel="noopener noreferrer"
                    >Download</el-button
                  >
                </template>
              </el-table-column>
              <el-table-column>
                <template #default="scope">
                  <el-button
                    type="danger"
                    @click="deleteRecord(recordList[scope.$index])"
                    >Delete</el-button
                  >
                </template>
              </el-table-column>
            </el-table>
            <el-dialog
              v-model="showingVideo"
              :align-center="true"
              title="Video"
            >
              <video :src="showingVideoSrc" controls></video>
            </el-dialog>
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped></style>
