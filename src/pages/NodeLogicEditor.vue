<template>
  <div class="node-logic-editor">
    <!-- 左侧输入字段 -->
    <div class="field-list input-list">
      <h3>输入字段</h3>
      <ul>
        <li v-for="field in inputFields" :key="field.id"
            :class="{ 'dep-highlight': isFieldDepended(field.id) }">
          <template v-if="isEditMode && selectedOutputField">
            <el-checkbox
              :model-value="isFieldDepended(field.id)"
              @change="checked => toggleInputDependency(field.id, checked)"
              style="margin-right: 8px"
            />
          </template>
          <template v-if="isEditMode">
            <el-input
              v-model="field.name"
              size="small"
              style="width: 120px"
              placeholder="字段名"
            />
          </template>
          <template v-else>
            {{ field.name }}
          </template>
          <el-button v-if="isEditMode" @click.stop="removeInputField(field.id)" type="text" size="small">删除</el-button>
        </li>
        <li v-if="inputFields.length === 0" class="empty-tip">暂无输入字段，请点击下方按钮添加</li>
      </ul>
      <el-button v-if="isEditMode" @click="addInputField">添加输入字段</el-button>
    </div>
    <!-- 中间逻辑区 -->
    <div class="logic-center" ref="logicCenterRef" style="position:relative;">
      <div v-if="selectedOutputField" style="flex:1; display:flex; flex-direction:column;">
        <h3>逻辑说明</h3>
        <textarea
          v-if="isEditMode && selectedOutputField"
          v-model="selectedOutputField.logic"
          class="logic-textarea"
          placeholder="请输入逻辑说明（支持Markdown）"
          @focus="console.log('[NodeLogicEditor] 渲染逻辑编辑框', selectedOutputField)"
        />
        <div v-else v-html="renderMarkdown(selectedOutputField.logic)" class="md-preview"></div>
      </div>
      <div v-else class="md-preview" style="color:#888;text-align:center;">请选择一个输出字段查看逻辑</div>
    </div>
    <!-- 右侧输出字段 -->
    <div class="field-list output-list">
      <h3>输出字段</h3>
      <ul>
        <li
          v-for="field in outputFields"
          :key="field.id"
          :class="{ selected: field.id === selectedOutputFieldId }"
          @click="selectOutputField(field.id)"
          class="output-field-item"
        >
          <template v-if="isEditMode">
            <el-input
              v-model="field.name"
              size="small"
              style="width: 120px"
              placeholder="字段名"
            />
          </template>
          <template v-else>
            {{ field.name }}
          </template>
          <el-button v-if="isEditMode" @click.stop="removeOutputField(field.id)" type="text" size="small">删除</el-button>
        </li>
        <li v-if="outputFields.length === 0" class="empty-tip">暂无输出字段，请点击下方按钮添加</li>
      </ul>
      <el-button v-if="isEditMode" @click="addOutputField">添加输出字段</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watchEffect, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { marked } from 'marked'
import * as models from './models.js'
const props = defineProps({
  node: Object, // Node对象
  isEditMode: Boolean
})
const emit = defineEmits(['add-input-field', 'add-output-field', 'remove-input-field', 'remove-output-field'])

const inputFields = computed(() => props.node?.inputFields || [])
const outputFields = computed(() => props.node?.outputFields || [])


const selectedOutputFieldId = ref(outputFields.value[0]?.id || null)
watch(outputFields, (val) => {
  if (!val.find(f => f.id === selectedOutputFieldId.value)) {
    selectedOutputFieldId.value = val[0]?.id || null
  }
})
const selectedOutputField = computed(() =>
  outputFields.value.find(f => f.id === selectedOutputFieldId.value) || null
)

function selectOutputField(id) {
  console.log('[NodeLogicEditor] selectOutputField', id)
  selectedOutputFieldId.value = id
  console.log('[NodeLogicEditor] selectedOutputField', selectedOutputField.value)
}
function addInputField() {
  emit('add-input-field', {
    id: 'input_' + Date.now(),
    name: '输入字段',
    dependendFieldIds: [],
    logic: ''
  })
}
function removeInputField(id) {
  const idx = props.node.inputFields.findIndex(f => f.id === id)
  if (idx !== -1) props.node.inputFields.splice(idx, 1)
}
function addOutputField() {
  emit('add-output-field', {
    id: 'output_' + Date.now(),
    name: '输出字段',
    dependendFieldIds: [],
    logic: ''
  })
}
function removeOutputField(id) {
  const idx = props.node.outputFields.findIndex(f => f.id === id)
  if (idx !== -1) props.node.outputFields.splice(idx, 1)
}
function renderMarkdown(md) {
  return marked(md || '')
}

const logicCenterRef = ref(null)

function isFieldDepended(inputId) {
  if (!selectedOutputField || !selectedOutputField.value || !Array.isArray(selectedOutputField.value.dependendFieldIds)) return false
  return selectedOutputField.value.dependendFieldIds.includes(inputId)
}
function toggleInputDependency(inputId, checked) {
  if (!selectedOutputField || !selectedOutputField.value) return
  if (!Array.isArray(selectedOutputField.value.dependendFieldIds)) {
    selectedOutputField.value.dependendFieldIds = []
  }
  let arr = selectedOutputField.value.dependendFieldIds
  if (checked) {
    if (!arr.includes(inputId)) {
      arr = arr.concat([inputId])
      selectedOutputField.value.dependendFieldIds = arr
    }
  } else {
    if (arr.includes(inputId)) {
      arr = arr.filter(id => id !== inputId)
      selectedOutputField.value.dependendFieldIds = arr
    }
  }
}

watch(selectedOutputField, (val) => {
  console.log('[NodeLogicEditor] selectedOutputField changed:', val)
})
</script>

<style scoped>
.node-logic-editor {
  display: flex;
  flex-direction: row;
  width: 100%;
  max-width: 100%;
  min-height: 600px;
  height: 80vh;
  max-height: 90vh;
  background: none;
  box-shadow: none;
  border-radius: 0;
  padding: 0;
  box-sizing: border-box;
  overflow-x: auto;
}
.field-list {
  width: 200px;
  max-width: 220px;
  min-width: 0;
  padding: 24px 12px 24px 0;
  max-height: 60vh;
  overflow-y: auto;
  background: none;
  border: none;
  box-shadow: none;
  word-break: break-all;
}
.input-list {
  border-right: 1.5px solid #f0f0f0;
}
.output-list {
  border-left: 1.5px solid #f0f0f0;
}
.field-list h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 18px;
  color: #222;
}
.field-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.field-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  padding: 12px 16px;
  border-radius: 8px;
  background: #fafbfc;
  transition: background 0.2s;
  font-size: 16px;
  line-height: 1.8;
  flex-wrap: wrap;
}
.field-list li.dep-highlight {
  background: #e6f7ff;
}
.field-list li:hover {
  background: #f0faff;
}
.el-input {
  flex: 1;
  font-size: 16px;
}
.el-checkbox {
  margin-right: 8px;
}
.empty-tip {
  color: #aaa;
  font-size: 15px;
  padding: 12px 0;
  text-align: center;
}
.logic-center {
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  padding: 32px 40px;
  height: 100%;
  min-height: 400px;
}
.logic-center h3 {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 18px;
  color: #222;
}
.logic-textarea {
  width: 100%;
  height: 100%;
  min-height: 320px;
  font-size: 17px;
  border-radius: 10px;
  border: 1.5px solid #e0e0e0;
  box-shadow: 0 2px 8px #f5f5f5;
  padding: 18px 20px;
  background: #fcfcfd;
  transition: border 0.2s;
  box-sizing: border-box;
  resize: none;
  flex: 1 1 0;
}
.el-input[type="textarea"]:focus, .md-preview:focus {
  border: 1.5px solid #409eff;
}
.md-preview {
  background: #f8fafd;
}
.el-button {
  border-radius: 6px;
  font-size: 15px;
  padding: 6px 18px;
}
.field-list .el-button[type="text"] {
  color: #409eff;
  font-size: 15px;
  padding: 0 8px;
  white-space: nowrap;
}
.field-list .el-button[type="text"]:hover {
  color: #f56c6c;
  background: #f9eaea;
}
.field-list .el-checkbox {
  margin-right: 10px;
}
.field-list li.selected {
  background: #e6f7ff;
  border: 1.5px solid #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.field-list li.selected:hover {
  background: #e6f7ff;
  border: 1.5px solid #40a9ff;
}
</style> 