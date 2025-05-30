<template>
  <div class="dag-editor-full">
    <div class="dag-mode-switch">
      <el-switch
        v-model="isEditMode"
        active-text="编辑模式"
        inactive-text="查看模式"
        inline-prompt
        style="margin-right: 24px;"
      />
    </div>
    <div class="dag-search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索字段名并高亮节点"
        clearable
        @input="handleSearch"
        @clear="clearSearchHighlight"
        size="small"
        class="search-input"
        style="width: 260px; margin-bottom: 8px;"
      />
    </div>
    <div v-if="showNodeMenu" class="node-menu" :style="{ left: nodeMenuPos.x + 'px', top: nodeMenuPos.y + 'px' }">
      <div class="node-menu-item node-menu-delete" @click="handleDeleteNodeFromMenu">删除节点</div>
      <div class="node-menu-item" @click="handleShowLogicFromMenu">查看逻辑</div>
      <div class="node-menu-item" @click="handleCopyNodeFromMenu">复制节点</div>
    </div>
    <div v-if="showAddNodeMenu" class="add-node-menu" :style="{ left: addNodeMenuPos.x + 'px', top: addNodeMenuPos.y + 'px' }">
      <div class="add-node-menu-item" @click="handleAddNodeAtMenu">添加节点</div>
    </div>
    <div ref="container" class="dag-graph-container" @contextmenu="onCanvasContextMenu"></div>
    <div v-if="editingNodeId && isEditMode" class="node-edit-bar">
      <input
        ref="editInputRef"
        v-model="editInputValue"
        class="node-edit-input"
        @keydown.enter="saveEdit"
        @keydown.esc="cancelEdit"
        @blur="saveEdit"
        maxlength="20"
        autofocus
      />
    </div>
    <div v-if="selectedNodeId" class="node-desc-bar">
      <template v-if="isEditMode">
        <el-input
          v-model="currentNodeDesc"
          type="textarea"
          :rows="2"
          placeholder="请输入节点描述"
          @blur="saveNodeDesc"
          class="node-desc-input"
        />
      </template>
      <template v-else>
        <div class="node-desc-text">{{ currentNodeDesc || '暂无描述' }}</div>
      </template>
    </div>
    <el-dialog v-model="showLogicEditor" title="节点逻辑查看/编辑" width="900px" :close-on-click-modal="false">
      <NodeLogicEditor
        v-if="currentNodeForLogic"
        :node="currentNodeForLogic"
        :isEditMode="isEditMode"
        @add-input-field="handleAddInputField"
        @add-output-field="handleAddOutputField"
      />
      <template #footer>
        <el-button @click="showLogicEditor = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch, computed, watchEffect } from 'vue'
import { Graph } from '@antv/x6'
import NodeLogicEditor from '@/pages/NodeLogicEditor.vue'
import * as models from './models.js'

// 全局 DAG 数据
const dagGraph = ref({
  nodes: [], // Node[]
})

const container = ref(null)
let graph = null
const selectedNodeId = ref(null)
const editingNodeId = ref(null)
const editInputValue = ref('')
const editInputRef = ref(null)
const isEditMode = ref(true)
const showLogicEditor = ref(false)
const currentNodeDesc = ref('')
const searchText = ref('')
const showAddNodeMenu = ref(false)
const addNodeMenuPos = ref({ x: 0, y: 0 })
let lastAddNodeCanvasPoint = { x: 0, y: 0 }
const showNodeMenu = ref(false)
const nodeMenuPos = ref({ x: 0, y: 0 })
const nodeMenuNodeId = ref(null)

// 节点label映射（辅助展示）
const nodeLabels = computed(() => {
  const map = {}
  dagGraph.value.nodes.forEach(n => { map[n.id] = n.label })
  return map
})

const currentNodeForLogic = computed(() => {
  if (!selectedNodeId.value) return null
  return dagGraph.value.nodes.find(n => n.id === selectedNodeId.value) || null
})

// 控制台debug
watchEffect(() => {
  console.log('当前节点:', currentNodeForLogic.value)
})

watch(editInputValue, (val) => {
  if (editingNodeId.value) {
    const node = graph.getCellById(editingNodeId.value)
    if (node) {
      node.setLabel(val)
    }
  }
})

watch(isEditMode, async (val) => {
  if (graph) {
    await nextTick()
    try {
      // 更新连线配置
      graph.options.connecting = {
        ...graph.options.connecting,
        allowEdge: false,
        allowNode: val,
        allowBlank: false,
        allowLoop: false,
        highlight: true,
        snap: true,
        validateConnection({ sourceCell, targetCell }) {
          return sourceCell.id !== targetCell.id && val
        },
        createEdge() {
          return graph.createEdge({
            attrs: {
              line: {
                stroke: '#A2B1C3',
                strokeWidth: 2,
                targetMarker: {
                  name: 'block',
                  width: 12,
                  height: 8,
                },
              },
            },
          })
        },
        edgeMovable: true
      }

      // 更新节点和连线的交互状态
      const nodes = graph.getNodes()
      if (nodes && nodes.length) {
        nodes.forEach(node => {
          if (node && node.setData) {
            node.setData({ draggable: true })
            node.attr('body/cursor', 'move')
            // 编辑模式下显示锚点，查看模式下隐藏锚点
            node.getPorts().forEach(port => {
              node.setPortProp(port.id, 'attrs/circle/style/display', val ? '' : 'none')
            })
          }
        })
      }

      const edges = graph.getEdges()
      if (edges && edges.length) {
        edges.forEach(edge => {
          if (edge && edge.attr) {
            edge.attr('line/cursor', 'pointer')
          }
        })
      }
    } catch (error) {
      console.warn('更新图形属性失败:', error)
    }
  }
})

watch(selectedNodeId, (newId) => {
  if (newId) {
    const node = dagGraph.value.nodes.find(n => n.id === newId)
    currentNodeDesc.value = node?.desc || ''
  } else {
    currentNodeDesc.value = ''
  }
})

function resizeGraph() {
  if (graph && container.value) {
    graph.resize(container.value.clientWidth, container.value.clientHeight)
  }
}

function clearNodeHighlight() {
  if (selectedNodeId.value) {
    const node = graph.getCellById(selectedNodeId.value)
    if (node) {
      node.setAttrs({ body: { stroke: '#5F95FF', strokeWidth: 1 } })
    }
    selectedNodeId.value = null
  }
}

function highlightNode(id) {
  const node = graph.getCellById(id)
  if (node) {
    node.setAttrs({ body: { stroke: '#f56c6c', strokeWidth: 3 } })
  }
}

function startEditNode(id) {
  if (!isEditMode.value) return
  editingNodeId.value = id
  editInputValue.value = nodeLabels.value[id] || '新节点'
  nextTick(() => {
    if (editInputRef.value) {
      editInputRef.value.focus()
      editInputRef.value.select()
    }
  })
}

function saveEdit() {
  if (editingNodeId.value && editInputValue.value.trim()) {
    nodeLabels.value[editingNodeId.value] = editInputValue.value.trim()
    const node = graph.getCellById(editingNodeId.value)
    if (node) node.setLabel(editInputValue.value.trim())
  }
  editingNodeId.value = null
}

function cancelEdit() {
  editingNodeId.value = null
}

function saveNodeDesc() {
  if (selectedNodeId.value) {
    const node = dagGraph.value.nodes.find(n => n.id === selectedNodeId.value)
    if (node) {
      node.desc = currentNodeDesc.value
    }
  }
}

onMounted(async () => {
  await nextTick()
  try {
    graph = new Graph({
      container: container.value,
      width: container.value.clientWidth,
      height: container.value.clientHeight,
      grid: true,
      scroller: {
        enabled: true,
        pannable: true,
        pageVisible: false,
        pageBreak: false,
        // autoResize: true // 如需自适应可打开
      },
      mousewheel: {
        enabled: true,
        modifiers: ['ctrl', 'meta'], // 按住 ctrl 或 command 时滚轮缩放
        minScale: 0.2,
        maxScale: 2,
      },
      connecting: {
        connector: 'smooth',
        anchor: 'center',
        connectionPoint: 'anchor',
        allowBlank: false,
        highlight: true,
        snap: true,
        allowLoop: false,
        allowNode: isEditMode.value,
        allowEdge: false,
        validateConnection({ sourceCell, targetCell }) {
          return sourceCell.id !== targetCell.id && isEditMode.value
        },
        createEdge() {
          return graph.createEdge({
            attrs: {
              line: {
                stroke: '#A2B1C3',
                strokeWidth: 2,
                targetMarker: {
                  name: 'block',
                  width: 12,
                  height: 8,
                },
              },
            },
          })
        },
        edgeMovable: true
      },
      selecting: {
        enabled: true,
        multiple: false,
        rubberband: true,
        showNodeSelectionBox: true,
        showEdgeSelectionBox: true,
      },
      keyboard: {
        enabled: true,
      },
      clipboard: {
        enabled: true,
      },
    })

    // 使画布支持直接鼠标左键拖动平移
    graph.enablePanning()

    window.addEventListener('resize', resizeGraph)

    // 选中节点高亮
    graph.on('node:click', ({ node }) => {
      if (selectedNodeId.value && selectedNodeId.value !== node.id) {
        clearNodeHighlight()
      }
      selectedNodeId.value = node.id
      highlightNode(node.id)
      // 点击节点时进入编辑状态，显示名称和描述输入框
      editingNodeId.value = node.id
      editInputValue.value = nodeLabels.value[node.id] || '新节点'
      currentNodeDesc.value = dagGraph.value.nodes.find(n => n.id === node.id)?.desc || ''
      nextTick(() => {
        if (editInputRef.value) {
          editInputRef.value.focus()
          editInputRef.value.select()
        }
      })
    })

    // 选中连线高亮
    graph.on('edge:click', ({ edge }) => {
      graph.getEdges().forEach(e => e.setAttrs({ line: { stroke: '#A2B1C3', strokeWidth: 2 } }))
      edge.setAttrs({ line: { stroke: '#f56c6c', strokeWidth: 3 } })
    })

    // 点击空白处取消选中
    graph.on('blank:click', () => {
      clearNodeHighlight()
      graph.getEdges().forEach(e => e.setAttrs({ line: { stroke: '#A2B1C3', strokeWidth: 2 } }))
    })

    // 右键删除连线
    graph.on('edge:contextmenu', ({ edge, e }) => {
      if (!isEditMode.value) return
      e.preventDefault()
      edge.remove()
    })

    // 双击节点，直接弹出逻辑编辑弹窗
    graph.on('node:dblclick', ({ node }) => {
      showLogicEditor.value = true
    })

    // 双击连线，直接删除
    graph.on('edge:dblclick', ({ edge }) => {
      if (!isEditMode.value) return
      edge.remove()
    })

    // 连线建立时更新节点关系
    graph.on('edge:connected', ({ edge }) => {
      const sourceNodeId = edge.getSourceCellId()
      const targetNodeId = edge.getTargetCellId()
      
      // 更新源节点的后置节点列表
      const sourceNode = dagGraph.value.nodes.find(n => n.id === sourceNodeId)
      if (sourceNode && !sourceNode.nextNodeIds.includes(targetNodeId)) {
        sourceNode.nextNodeIds.push(targetNodeId)
      }
      
      // 更新目标节点的前置节点列表
      const targetNode = dagGraph.value.nodes.find(n => n.id === targetNodeId)
      if (targetNode && !targetNode.preNodeIds.includes(sourceNodeId)) {
        targetNode.preNodeIds.push(sourceNodeId)
      }
    })

    // 连线删除时更新节点关系
    graph.on('edge:removed', ({ edge }) => {
      const sourceNodeId = edge.getSourceCellId()
      const targetNodeId = edge.getTargetCellId()
      
      // 更新源节点的后置节点列表
      const sourceNode = dagGraph.value.nodes.find(n => n.id === sourceNodeId)
      if (sourceNode) {
        sourceNode.nextNodeIds = sourceNode.nextNodeIds.filter(id => id !== targetNodeId)
      }
      
      // 更新目标节点的前置节点列表
      const targetNode = dagGraph.value.nodes.find(n => n.id === targetNodeId)
      if (targetNode) {
        targetNode.preNodeIds = targetNode.preNodeIds.filter(id => id !== sourceNodeId)
      }
    })

    // 节点右键菜单
    graph.on('node:contextmenu', onNodeContextMenu)
  } catch (error) {
    console.error('初始化图形失败:', error)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeGraph)
  if (graph) {
    try {
      graph.dispose()
    } catch (error) {
      console.warn('清理图形实例失败:', error)
    }
  }
})

function generatePorts() {
  const positions = ['top', 'right', 'bottom', 'left']
  const items = []
  positions.forEach(pos => {
    for (let i = 0; i < 4; i++) {
      items.push({ id: `${pos}_${i}_${Date.now()}_${Math.floor(Math.random()*10000)}`, group: pos })
    }
  })
  return items
}

function addNode(pos) {
  if (!isEditMode.value) return
  const id = `${Date.now()}_${Math.floor(Math.random()*10000)}`
  dagGraph.value.nodes.push({
    id,
    label: '新节点',
    inputFields: [],
    outputFields: [],
    preNodeIds: [],
    nextNodeIds: [],
    desc: ''
  })
  graph.addNode({
    id,
    x: pos && pos.x !== undefined ? pos.x : Math.random() * 600,
    y: pos && pos.y !== undefined ? pos.y : Math.random() * 400,
    width: 100,
    height: 40,
    label: '新节点',
    attrs: {
      body: {
        stroke: '#5F95FF',
        strokeWidth: 1,
        fill: '#fff',
      },
      label: {
        fontSize: 14,
        fill: '#333',
      }
    },
    data: {
      label: '新节点',
    },
    ports: {
      groups: {
        top: {
          position: {
            name: 'top',
            args: { dx: 0 }
          },
          attrs: {
            circle: {
              r: 3,
              magnet: true,
              stroke: '#bfcbd9',
              strokeWidth: 1,
              fill: '#fff',
              style: {
                pointerEvents: 'all',
                opacity: 0.18,
                transition: 'opacity 0.2s',
              }
            }
          }
        },
        right: {
          position: {
            name: 'right',
            args: { dy: 0 }
          },
          attrs: {
            circle: {
              r: 3,
              magnet: true,
              stroke: '#bfcbd9',
              strokeWidth: 1,
              fill: '#fff',
              style: {
                pointerEvents: 'all',
                opacity: 0.18,
                transition: 'opacity 0.2s',
              }
            }
          }
        },
        bottom: {
          position: {
            name: 'bottom',
            args: { dx: 0 }
          },
          attrs: {
            circle: {
              r: 3,
              magnet: true,
              stroke: '#bfcbd9',
              strokeWidth: 1,
              fill: '#fff',
              style: {
                pointerEvents: 'all',
                opacity: 0.18,
                transition: 'opacity 0.2s',
              }
            }
          }
        },
        left: {
          position: {
            name: 'left',
            args: { dy: 0 }
          },
          attrs: {
            circle: {
              r: 3,
              magnet: true,
              stroke: '#bfcbd9',
              strokeWidth: 1,
              fill: '#fff',
              style: {
                pointerEvents: 'all',
                opacity: 0.18,
                transition: 'opacity 0.2s',
              }
            }
          }
        }
      },
      items: generatePorts()
    }
  })
}

function deleteNode() {
  if (!isEditMode.value) return
  if (selectedNodeId.value) {
    const node = graph.getCellById(selectedNodeId.value)
    if (node) node.remove()
    delete nodeLabels.value[selectedNodeId.value]
    selectedNodeId.value = null
  }
}

function handleAddInputField(field) {
  const node = dagGraph.value.nodes.find(n => n.id === selectedNodeId.value)
  if (node) node.inputFields.push(field)
}

function handleAddOutputField(field) {
  const node = dagGraph.value.nodes.find(n => n.id === selectedNodeId.value)
  if (node) node.outputFields.push(field)
}

function handleSearch() {
  // 先清除所有高亮
  if (graph) {
    graph.getNodes().forEach(node => {
      node.setAttrs({ body: { stroke: '#5F95FF', strokeWidth: 1 } })
    })
  }
  if (!searchText.value.trim()) return
  // 遍历所有节点，查找字段名
  dagGraph.value.nodes.forEach(node => {
    const match = [...(node.inputFields || []), ...(node.outputFields || [])].some(f => f.name === searchText.value.trim())
    if (match && graph) {
      const gNode = graph.getCellById(node.id)
      if (gNode) {
        gNode.setAttrs({ body: { stroke: '#faad14', strokeWidth: 3 } })
      }
    }
  })
}

function clearSearchHighlight() {
  if (graph) {
    graph.getNodes().forEach(node => {
      node.setAttrs({ body: { stroke: '#5F95FF', strokeWidth: 1 } })
    })
  }
}

function onCanvasContextMenu(e) {
  e.preventDefault()
  // 只在编辑模式下允许
  if (!isEditMode.value) return
  showAddNodeMenu.value = true
  addNodeMenuPos.value = { x: e.clientX, y: e.clientY }
  // 使用X6的坐标转换，保证节点出现在画布实际位置
  if (graph) {
    const local = graph.clientToLocal(e.clientX, e.clientY)
    lastAddNodeCanvasPoint = { x: local.x, y: local.y }
  }
}

function handleAddNodeAtMenu() {
  addNode(lastAddNodeCanvasPoint)
  showAddNodeMenu.value = false
}

// 节点右键菜单事件
function onNodeContextMenu({ node, e }) {
  if (!isEditMode.value) return
  e.preventDefault()
  showNodeMenu.value = true
  nodeMenuPos.value = { x: e.clientX, y: e.clientY }
  nodeMenuNodeId.value = node.id
}

function handleDeleteNodeFromMenu() {
  if (!isEditMode.value || !nodeMenuNodeId.value) return
  const node = graph.getCellById(nodeMenuNodeId.value)
  if (node) node.remove()
  delete nodeLabels.value[nodeMenuNodeId.value]
  selectedNodeId.value = null
  showNodeMenu.value = false
}

function handleShowLogicFromMenu() {
  selectedNodeId.value = nodeMenuNodeId.value
  showLogicEditor.value = true
  showNodeMenu.value = false
}

function handleCopyNodeFromMenu() {
  const node = dagGraph.value.nodes.find(n => n.id === nodeMenuNodeId.value)
  if (node) {
    const id = `${Date.now()}_${Math.floor(Math.random()*10000)}`
    const newNode = JSON.parse(JSON.stringify(node))
    newNode.id = id
    newNode.label = node.label
    // 位置偏移
    let x = 100, y = 100
    if (graph && graph.getCellById(node.id)) {
      const oldNode = graph.getCellById(node.id)
      x = (oldNode.getPosition().x || 0) + 40
      y = (oldNode.getPosition().y || 0) + 40
    }
    dagGraph.value.nodes.push(newNode)
    graph.addNode({
      id,
      x,
      y,
      width: 100,
      height: 40,
      label: newNode.label,
      attrs: {
        body: {
          stroke: '#5F95FF',
          strokeWidth: 1,
          fill: '#fff',
        },
        label: {
          fontSize: 14,
          fill: '#333',
        }
      },
      data: {
        label: newNode.label,
      },
      ports: {
        groups: {
          top: {
            position: {
              name: 'top',
              args: { dx: 0 }
            },
            attrs: {
              circle: {
                r: 3,
                magnet: true,
                stroke: '#bfcbd9',
                strokeWidth: 1,
                fill: '#fff',
                style: {
                  pointerEvents: 'all',
                  opacity: 0.18,
                  transition: 'opacity 0.2s',
                }
              }
            }
          },
          right: {
            position: {
              name: 'right',
              args: { dy: 0 }
            },
            attrs: {
              circle: {
                r: 3,
                magnet: true,
                stroke: '#bfcbd9',
                strokeWidth: 1,
                fill: '#fff',
                style: {
                  pointerEvents: 'all',
                  opacity: 0.18,
                  transition: 'opacity 0.2s',
                }
              }
            }
          },
          bottom: {
            position: {
              name: 'bottom',
              args: { dx: 0 }
            },
            attrs: {
              circle: {
                r: 3,
                magnet: true,
                stroke: '#bfcbd9',
                strokeWidth: 1,
                fill: '#fff',
                style: {
                  pointerEvents: 'all',
                  opacity: 0.18,
                  transition: 'opacity 0.2s',
                }
              }
            }
          },
          left: {
            position: {
              name: 'left',
              args: { dy: 0 }
            },
            attrs: {
              circle: {
                r: 3,
                magnet: true,
                stroke: '#bfcbd9',
                strokeWidth: 1,
                fill: '#fff',
                style: {
                  pointerEvents: 'all',
                  opacity: 0.18,
                  transition: 'opacity 0.2s',
                }
              }
            }
          }
        },
        items: generatePorts()
      }
    })
  }
  showNodeMenu.value = false
}

// 点击其他区域关闭菜单
window.addEventListener('click', () => { showAddNodeMenu.value = false; showNodeMenu.value = false })
</script>

<style scoped>
.dag-editor-full {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
}
.dag-mode-switch {
  position: absolute;
  top: 16px;
  right: 32px;
  z-index: 30;
}
.dag-graph-container {
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
  border: 1px solid #eee;
}
.dag-toolbar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 0;
  background: #fff;
  border-top: 1px solid #eee;
  box-shadow: 0 -2px 8px #f5f5f5;
  gap: 16px;
  z-index: 20;
}
.node-edit-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f8f8f8;
  border-top: 1px solid #eee;
  padding: 18px 0 8px 0;
}
.node-edit-input {
  font-size: 16px;
  padding: 6px 16px;
  border: 1px solid #5F95FF;
  border-radius: 4px;
  outline: none;
  min-width: 120px;
  max-width: 240px;
  background: #fff;
}
.logic-btn-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px 0 0 0;
  background: none;
}
.node-desc-bar {
  width: 100%;
  padding: 16px 24px;
  background: #f8f8f8;
  border-top: 1px solid #eee;
  box-sizing: border-box;
}
.node-desc-text {
  font-size: 15px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
}
.node-desc-input .el-textarea__inner {
  font-size: 14px;
  min-height: 36px !important;
  background: #fafbfc;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  box-shadow: none;
  transition: border 0.2s;
  padding: 8px 12px;
}
.node-desc-input .el-textarea__inner:focus {
  border: 1.5px solid #5F95FF;
  background: #fff;
}
.dag-search-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px 0 0 0;
  background: #fff;
  z-index: 11;
}
.search-input {
  font-size: 14px;
}
.add-node-menu {
  position: fixed;
  z-index: 1000;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 2px 8px #eee;
  min-width: 100px;
  padding: 4px 0;
}
.add-node-menu-item {
  padding: 8px 18px;
  cursor: pointer;
  font-size: 15px;
  color: #333;
  transition: background 0.2s;
}
.add-node-menu-item:hover {
  background: #f5f7fa;
}
.node-menu {
  position: fixed;
  z-index: 1001;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 2px 8px #eee;
  min-width: 120px;
  padding: 4px 0;
}
.node-menu-item {
  padding: 8px 18px;
  cursor: pointer;
  font-size: 15px;
  color: #333;
  transition: background 0.2s;
}
.node-menu-item:hover {
  background: #f5f7fa;
}
.node-menu-delete {
  color: #f56c6c;
  font-weight: bold;
}
</style> 