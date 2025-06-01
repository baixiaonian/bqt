<template>
  <div class="dag-editor-full"
    v-loading="isLoading || isSaving || isDeleting"
    element-loading-text="加载中..."
    element-loading-background="rgba(255,255,255,0.6)"
  >
    <!-- 左侧竖排按钮 -->
    <div class="dag-list-float-btn" @click.stop="toggleDagListPanel">
      <span>图<br>列<br>表</span>
    </div>
    <!-- 图列表面板 -->
    <div class="dag-list-panel" :class="{ show: showDagListPanel }" @click.stop>
      <div class="dag-list-title">图列表</div>
      <ul class="dag-list-ul">
        <li
          v-for="item in dagList"
          :key="item.id"
          :class="{ active: item.id === currentDagId }"
          class="dag-list-item"
          @click="onSelectDag(item.id)"
          @mouseenter="hoverDagId = item.id"
          @mouseleave="hoverDagId = null"
          style="position:relative;"
        >
          <div class="dag-list-item-main">
            <template v-if="editingDagId === item.id">
              <el-input
                v-model="editingDagName"
                class="dag-list-edit-input"
                size="small"
                @blur="saveEditDagName(item)"
                @keydown.enter="saveEditDagName(item)"
                @keydown.esc="editingDagId = null"
                style="width:120px;"
                :disabled="isSaving"
              />
            </template>
            <template v-else>
              <div class="dag-list-item-title" @dblclick.stop="startEditDagName(item)">{{ item.name }}</div>
            </template>
          </div>
          <el-button
            v-if="hoverDagId === item.id"
            class="dag-list-delete-btn"
            type="danger"
            size="small"
            circle
            @click.stop="onDeleteDag(item.id)"
            :icon="Delete"
            :loading="isDeleting"
            :disabled="isDeleting"
          />
        </li>
        <!-- 新建图项 -->
        <li class="dag-list-item dag-list-add-item" @click="onAddDag">
          <div class="dag-list-item-main dag-list-add-main">
            <el-icon class="dag-list-add-plus"><Plus /></el-icon>
          </div>
        </li>
      </ul>
      <div class="dag-list-plus-bar">
        <el-button class="dag-list-plus-btn" circle type="primary" plain @click="onAddDag" :loading="isSaving" :disabled="isSaving">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
    </div>
    <div class="dag-toolbar-bar">
      <div class="dag-search-bar">
        <el-input
          v-model="searchText"
          placeholder="搜索字段名并高亮节点"
          clearable
          @input="handleSearch"
          @clear="clearSearchHighlight"
          size="small"
          class="search-input"
          style="width: 260px; margin-bottom: 0;"
        />
      </div>
      <div class="dag-toolbar-group">
        <el-button
          class="dag-save-btn-beauty"
          type="primary"
          :loading="isSaving"
          @click="saveDag"
          :disabled="isSaving"
        >保存</el-button>
        <el-button
          class="dag-export-btn-beauty"
          type="default"
          @click="exportDagAsJson"
          :disabled="!dagGraph.id"
        >导出</el-button>
        <el-button
          class="dag-import-btn-beauty"
          type="default"
          @click="onImportDagClick"
        >导入</el-button>
        <input
          ref="importInputRef"
          type="file"
          accept=".json"
          style="display:none"
          @change="onImportDagFile"
        />
        <div class="dag-edit-switch-scale">
          <el-switch
            v-model="isEditMode"
            active-text="编辑模式"
            inactive-text="查看模式"
            inline-prompt
            class="dag-edit-switch"
          />
        </div>
      </div>
    </div>
    <div class="dag-ops-tip">
      <span class="ops-tip-key">新建节点：</span>右键画板空白区域<br>
      <span class="ops-tip-key">查看节点内部逻辑：</span>双击节点<br>
      <span class="ops-tip-key">节点名称、描述修改：</span>单击节点，画布下方修改<br>
      <span class="ops-tip-key">删除、复制、查看节点逻辑：</span>右键节点<br>
      <span class="ops-tip-key">删除连线：</span>左键双击连线<br>
      <span class="ops-tip-key">节点内部逻辑编辑：</span>选中输出字段；勾选依赖的输入，中间文本框中编辑<br>
      <span class="ops-tip-key">画布移动：</span>鼠标左键长按画布空白区域移动<br>
      <span class="ops-tip-key">缩放：</span>ctrl/command + 鼠标滚轮<br>
      <span class="ops-tip-key">图名称修改：</span>双击图列表图名称，修改后回车
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
        maxlength="50"
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
    <el-dialog
      v-model="showLogicEditor"
      title="节点逻辑查看/编辑"
      width="95vw"
      :close-on-click-modal="false"
      style="max-width:1600px; margin:0 auto; border-radius:16px;"
    >
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

    <!-- 右键空白区域菜单 -->
    <div v-if="showAddNodeMenu" class="add-node-menu" :style="{ left: addNodeMenuPos.x + 'px', top: addNodeMenuPos.y + 'px' }">
      <div class="add-node-menu-item" @click="handleAddNodeAtMenu">新建节点</div>
    </div>

    <!-- 右键节点菜单 -->
    <div v-if="showNodeMenu" class="node-menu" :style="{ left: nodeMenuPos.x + 'px', top: nodeMenuPos.y + 'px' }">
      <div class="node-menu-item" @click="handleShowLogicFromMenu">查看/编辑逻辑</div>
      <div class="node-menu-item" @click="handleCopyNodeFromMenu">复制节点</div>
      <div class="node-menu-item node-menu-delete" @click="handleDeleteNodeFromMenu">删除节点</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch, computed, watchEffect } from 'vue'
import { Graph } from '@antv/x6'
import NodeLogicEditor from '@/pages/NodeLogicEditor.vue'
import * as models from './models.js'
import { ElMessageBox, ElMessage, ElLoading } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'

// 多图相关
const dagList = ref([])           // 图列表
const currentDagId = ref(null)    // 当前选中图的id
const isSaving = ref(false)
const isLoading = ref(false)
const isDeleting = ref(false)

// 全局 DAG 数据
const dagGraph = ref({
  id: '',
  name: '',
  desc: '',
  nodes: [],
  edges: []
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
const hoverDagId = ref(null)
const editingDagId = ref(null)
const editingDagName = ref('')
const showDagListPanel = ref(false)
const importInputRef = ref(null)
const is_change = ref(false)

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

// // 控制台debug
// watchEffect(() => {
//   console.log('当前节点:', currentNodeForLogic.value)
// })

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

// 监听所有会更改图的操作，设置 is_change = true
function markChanged() {
  if (isEditMode.value) is_change.value = true
}

function saveEdit() {
  if (editingNodeId.value && editInputValue.value.trim()) {
    nodeLabels.value[editingNodeId.value] = editInputValue.value.trim()
    const node = graph.getCellById(editingNodeId.value)
    if (node) node.setLabel(editInputValue.value.trim())
  }
  editingNodeId.value = null
  markChanged()
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
  markChanged()
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

    // 注册连线建立/删除时的修改标志
    graph.on('edge:connected', () => { markChanged() })
    graph.on('edge:removed', () => { markChanged() })

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

    // 渲染节点
    if (graph && dagGraph.value.nodes && dagGraph.value.nodes.length > 0) {
      dagGraph.value.nodes.forEach(node => {
        // 兼容老数据：无ports或数量不对时自动生成
        let ports = node.ports
        if (!ports || !ports.items || ports.items.length !== 32) {
          ports = {
            groups: {
              top: {
                position: { name: 'top', args: { dx: 0 } },
                attrs: {
                  circle: {
                    r: 2.5,
                    magnet: true,
                    stroke: '#409EFF',
                    strokeWidth: 1,
                    fill: '#fff',
                    style: {
                      pointerEvents: 'all',
                      opacity: 0.3,
                      transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                    }
                  }
                }
              },
              right: {
                position: { name: 'right', args: { dy: 0 } },
                attrs: {
                  circle: {
                    r: 2.5,
                    magnet: true,
                    stroke: '#409EFF',
                    strokeWidth: 1,
                    fill: '#fff',
                    style: {
                      pointerEvents: 'all',
                      opacity: 0.3,
                      transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                    }
                  }
                }
              },
              bottom: {
                position: { name: 'bottom', args: { dx: 0 } },
                attrs: {
                  circle: {
                    r: 2.5,
                    magnet: true,
                    stroke: '#409EFF',
                    strokeWidth: 1,
                    fill: '#fff',
                    style: {
                      pointerEvents: 'all',
                      opacity: 0.3,
                      transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                    }
                  }
                }
              },
              left: {
                position: { name: 'left', args: { dy: 0 } },
                attrs: {
                  circle: {
                    r: 2.5,
                    magnet: true,
                    stroke: '#409EFF',
                    strokeWidth: 1,
                    fill: '#fff',
                    style: {
                      pointerEvents: 'all',
                      opacity: 0.3,
                      transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                    }
                  }
                }
              }
            },
            items: generatePorts(node.id)
          }
        }
        graph.addNode({
          id: node.id,
          x: typeof node.x === 'number' ? node.x : Math.random() * 600,
          y: typeof node.y === 'number' ? node.y : Math.random() * 400,
          width: 200,
          height: 66,
          label: node.label,
          attrs: {
            body: {
              stroke: '#5F95FF',
              strokeWidth: 1,
              fill: '#fff',
              rx: 12,
              ry: 12,
              filter: 'drop-shadow(0 2px 8px #e6f7ff)',
            },
            label: {
              fontSize: 16,
              fill: '#222',
              fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
              fontWeight: 500,
            }
          },
          data: {
            label: node.label,
          },
          ports
        })
      })
      // 渲染完所有节点后，统一根据isEditMode隐藏/显示锚点
      graph.getNodes().forEach(node => {
        node.getPorts().forEach(port => {
          node.setPortProp(port.id, 'attrs/circle/style/display', isEditMode.value ? '' : 'none')
        })
      })
      // 调试：打印所有节点的ports
      console.log('所有节点锚点：', graph.getNodes().map(n => ({ id: n.id, ports: n.getPorts() })))
      console.log('edges:', dagGraph.value.edges)
      // 渲染连线（优先用edges）
      if (dagGraph.value.edges && dagGraph.value.edges.length > 0) {
        dagGraph.value.edges.forEach(edge => {
          const sourceNode = graph.getCellById(edge.source)
          const targetNode = graph.getCellById(edge.target)
          const sourcePortExists = sourceNode && sourceNode.getPorts().some(p => p.id === edge.sourcePort)
          const targetPortExists = targetNode && targetNode.getPorts().some(p => p.id === edge.targetPort)
          if (sourceNode && targetNode && sourcePortExists && targetPortExists) {
            graph.addEdge({
              source: { cell: edge.source, port: edge.sourcePort },
              target: { cell: edge.target, port: edge.targetPort },
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
          } else {
            console.warn('连线锚点不存在，跳过:', edge)
          }
        })
      } else {
        // 兼容老数据：仅用nextNodeIds渲染
        dagGraph.value.nodes.forEach(node => {
          if (node.nextNodeIds && node.nextNodeIds.length > 0) {
            node.nextNodeIds.forEach(targetId => {
              if (graph.getCellById(node.id) && graph.getCellById(targetId)) {
                graph.addEdge({
                  source: node.id,
                  target: targetId,
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
              }
            })
          }
        })
      }
    }
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

function generatePorts(nodeId) {
  const items = []
  for (let i = 0; i < 12; i++) {
    items.push({ id: `top_${i}_${nodeId}`, group: 'top' })
  }
  for (let i = 0; i < 12; i++) {
    items.push({ id: `bottom_${i}_${nodeId}`, group: 'bottom' })
  }
  for (let i = 0; i < 4; i++) {
    items.push({ id: `left_${i}_${nodeId}`, group: 'left' })
  }
  for (let i = 0; i < 4; i++) {
    items.push({ id: `right_${i}_${nodeId}`, group: 'right' })
  }
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
    width: 200,
    height: 66,
    label: '新节点',
    attrs: {
      body: {
        stroke: '#5F95FF',
        strokeWidth: 1,
        fill: '#fff',
        rx: 12,
        ry: 12,
        filter: 'drop-shadow(0 2px 8px #e6f7ff)',
      },
      label: {
        fontSize: 16,
        fill: '#222',
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
        fontWeight: 500,
      }
    },
    data: {
      label: '新节点',
    },
    ports: {
      groups: {
        top: {
          position: { name: 'top', args: { dx: 0 } },
          attrs: {
            circle: {
              r: 2.5,
              magnet: true,
              stroke: '#409EFF',
              strokeWidth: 1,
              fill: '#fff',
              style: {
                pointerEvents: 'all',
                opacity: 0.3,
                transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
              }
            }
          }
        },
        right: {
          position: { name: 'right', args: { dy: 0 } },
          attrs: {
            circle: {
              r: 2.5,
              magnet: true,
              stroke: '#409EFF',
              strokeWidth: 1,
              fill: '#fff',
              style: {
                pointerEvents: 'all',
                opacity: 0.3,
                transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
              }
            }
          }
        },
        bottom: {
          position: { name: 'bottom', args: { dx: 0 } },
          attrs: {
            circle: {
              r: 2.5,
              magnet: true,
              stroke: '#409EFF',
              strokeWidth: 1,
              fill: '#fff',
              style: {
                pointerEvents: 'all',
                opacity: 0.3,
                transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
              }
            }
          }
        },
        left: {
          position: { name: 'left', args: { dy: 0 } },
          attrs: {
            circle: {
              r: 2.5,
              magnet: true,
              stroke: '#409EFF',
              strokeWidth: 1,
              fill: '#fff',
              style: {
                pointerEvents: 'all',
                opacity: 0.3,
                transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
              }
            }
          }
        }
      },
      items: generatePorts(id)
    }
  })
  markChanged()
}

function deleteNode() {
  if (!isEditMode.value) return
  if (selectedNodeId.value) {
    const node = graph.getCellById(selectedNodeId.value)
    if (node) node.remove()
    delete nodeLabels.value[selectedNodeId.value]
    selectedNodeId.value = null
  }
  markChanged()
}

function handleAddInputField(field) {
  const node = dagGraph.value.nodes.find(n => n.id === selectedNodeId.value)
  if (node) node.inputFields.push(field)
  markChanged()
}

function handleAddOutputField(field) {
  const node = dagGraph.value.nodes.find(n => n.id === selectedNodeId.value)
  if (node) node.outputFields.push(field)
  markChanged()
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
  markChanged()
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
  markChanged()
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
      width: 200,
      height: 66,
      label: newNode.label,
      attrs: {
        body: {
          stroke: '#5F95FF',
          strokeWidth: 1,
          fill: '#fff',
          rx: 12,
          ry: 12,
          filter: 'drop-shadow(0 2px 8px #e6f7ff)',
        },
        label: {
          fontSize: 16,
          fill: '#222',
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
          fontWeight: 500,
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
                r: 2.5,
                magnet: true,
                stroke: '#409EFF',
                strokeWidth: 1,
                fill: '#fff',
                style: {
                  pointerEvents: 'all',
                  opacity: 0.3,
                  transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
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
                r: 2.5,
                magnet: true,
                stroke: '#409EFF',
                strokeWidth: 1,
                fill: '#fff',
                style: {
                  pointerEvents: 'all',
                  opacity: 0.3,
                  transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
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
                r: 2.5,
                magnet: true,
                stroke: '#409EFF',
                strokeWidth: 1,
                fill: '#fff',
                style: {
                  pointerEvents: 'all',
                  opacity: 0.3,
                  transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
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
                r: 2.5,
                magnet: true,
                stroke: '#409EFF',
                strokeWidth: 1,
                fill: '#fff',
                style: {
                  pointerEvents: 'all',
                  opacity: 0.3,
                  transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                }
              }
            }
          }
        },
        items: generatePorts(id)
      }
    })
  }
  showNodeMenu.value = false
}

// 点击其他区域关闭菜单
window.addEventListener('click', () => { showAddNodeMenu.value = false; showNodeMenu.value = false })

// 多图API
async function fetchDagList() {
  isLoading.value = true
  try {
    const res = await fetch('/api/dag-list')
    const arr = await res.json()
    dagList.value = [] // 先清空
    dagList.value = arr // 再赋值
    window.dagList = dagList
  } finally {
    isLoading.value = false
  }
}

function syncNodeEdgesFromCanvas(nodes) {
  // 先清空
  nodes.forEach(n => {
    n.nextNodeIds = []
    n.preNodeIds = []
  })
  if (!graph) return
  graph.getEdges().forEach(edge => {
    const source = edge.getSourceCellId()
    const target = edge.getTargetCellId()
    const sourceNode = nodes.find(n => n.id === source)
    const targetNode = nodes.find(n => n.id === target)
    if (sourceNode && targetNode) {
      sourceNode.nextNodeIds.push(target)
      targetNode.preNodeIds.push(source)
    }
  })
}

function getGraphEdgesFromCanvas() {
  if (!graph) return []
  return graph.getEdges().map(edge => {
    const source = edge.getSource()
    const target = edge.getTarget()
    return {
      source: source.cell,
      sourcePort: source.port || null,
      target: target.cell,
      targetPort: target.port || null
    }
  })
}

async function saveDag() {
  if (!dagGraph.value.id) return
  isSaving.value = true
  // 保存前同步画布节点和连线关系
  dagGraph.value.nodes = getGraphNodesFromCanvas()
  syncNodeEdgesFromCanvas(dagGraph.value.nodes)
  dagGraph.value.edges = getGraphEdgesFromCanvas()
  const saveData = {
    id: dagGraph.value.id,
    name: dagGraph.value.name || '未命名图',
    data: JSON.stringify(dagGraph.value)
  }
  console.log('[保存DAG] 请求数据:', JSON.stringify(saveData, null, 2))
  try {
    const res = await fetch('/api/save-dag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(saveData)
    })
    if (!res.ok) {
      const text = await res.text()
      console.log('[保存DAG] 接口响应异常:', res.status, text)
      throw new Error('保存失败: ' + res.status)
    }
    const result = await res.json()
    console.log('[保存DAG] 成功:', result)
    await fetchDagListAndSwitchToCurrent()
    is_change.value = false
  } catch (err) {
    console.log('[保存DAG] 异常:', err)
  } finally {
    isSaving.value = false
  }
}

async function fetchDag(id) {
  isLoading.value = true
  try {
    if (graph) {
      graph.clearCells()
    }
    const res = await fetch(`/api/load-dag?id=${id}`)
    const dag = await res.json()
    if (dag && dag.data) {
      const data = JSON.parse(dag.data)
      dagGraph.value = { ...data, id: dag.id, name: dag.name }
      currentDagId.value = dag.id
      // 渲染节点
      if (graph && dagGraph.value.nodes && dagGraph.value.nodes.length > 0) {
        dagGraph.value.nodes.forEach(node => {
          // 兼容老数据：无ports或数量不对时自动生成
          let ports = node.ports
          if (!ports || !ports.items || ports.items.length !== 32) {
            ports = {
              groups: {
                top: {
                  position: { name: 'top', args: { dx: 0 } },
                  attrs: {
                    circle: {
                      r: 2.5,
                      magnet: true,
                      stroke: '#409EFF',
                      strokeWidth: 1,
                      fill: '#fff',
                      style: {
                        pointerEvents: 'all',
                        opacity: 0.3,
                        transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                      }
                    }
                  }
                },
                right: {
                  position: { name: 'right', args: { dy: 0 } },
                  attrs: {
                    circle: {
                      r: 2.5,
                      magnet: true,
                      stroke: '#409EFF',
                      strokeWidth: 1,
                      fill: '#fff',
                      style: {
                        pointerEvents: 'all',
                        opacity: 0.3,
                        transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                      }
                    }
                  }
                },
                bottom: {
                  position: { name: 'bottom', args: { dx: 0 } },
                  attrs: {
                    circle: {
                      r: 2.5,
                      magnet: true,
                      stroke: '#409EFF',
                      strokeWidth: 1,
                      fill: '#fff',
                      style: {
                        pointerEvents: 'all',
                        opacity: 0.3,
                        transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                      }
                    }
                  }
                },
                left: {
                  position: { name: 'left', args: { dy: 0 } },
                  attrs: {
                    circle: {
                      r: 2.5,
                      magnet: true,
                      stroke: '#409EFF',
                      strokeWidth: 1,
                      fill: '#fff',
                      style: {
                        pointerEvents: 'all',
                        opacity: 0.3,
                        transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                      }
                    }
                  }
                }
              },
              items: generatePorts(node.id)
            }
          }
          graph.addNode({
            id: node.id,
            x: typeof node.x === 'number' ? node.x : Math.random() * 600,
            y: typeof node.y === 'number' ? node.y : Math.random() * 400,
            width: 200,
            height: 66,
            label: node.label,
            attrs: {
              body: {
                stroke: '#5F95FF',
                strokeWidth: 1,
                fill: '#fff',
                rx: 12,
                ry: 12,
                filter: 'drop-shadow(0 2px 8px #e6f7ff)',
              },
              label: {
                fontSize: 16,
                fill: '#222',
                fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
                fontWeight: 500,
              }
            },
            data: {
              label: node.label,
            },
            ports
          })
        })
        // 渲染完所有节点后，统一根据isEditMode隐藏/显示锚点
        graph.getNodes().forEach(node => {
          node.getPorts().forEach(port => {
            node.setPortProp(port.id, 'attrs/circle/style/display', isEditMode.value ? '' : 'none')
          })
        })
        // 渲染连线（优先用edges）
        if (dagGraph.value.edges && dagGraph.value.edges.length > 0) {
          dagGraph.value.edges.forEach(edge => {
            const sourceNode = graph.getCellById(edge.source)
            const targetNode = graph.getCellById(edge.target)
            const sourcePortExists = sourceNode && sourceNode.getPorts().some(p => p.id === edge.sourcePort)
            const targetPortExists = targetNode && targetNode.getPorts().some(p => p.id === edge.targetPort)
            if (sourceNode && targetNode && sourcePortExists && targetPortExists) {
              graph.addEdge({
                source: { cell: edge.source, port: edge.sourcePort },
                target: { cell: edge.target, port: edge.targetPort },
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
            } else {
              console.warn('连线锚点不存在，跳过:', edge)
            }
          })
        }
      }
    }
    is_change.value = false
  } finally {
    isLoading.value = false
  }
}

async function fetchDagListAndSwitchToCurrent() {
  await fetchDagList()
  
  if (dagGraph.value.id) {
    const found = dagList.value.find(item => item.id === dagGraph.value.id)
    if (found) {
      currentDagId.value = dagGraph.value.id
    }
  }
}

function getGraphNodesFromCanvas() {
  if (!graph) return []
  return graph.getNodes().map(node => {
    // 从dagGraph中获取最新数据
    const nodeData = dagGraph.value.nodes.find(n => n.id === node.id) || {}
    return {
      id: node.id,
      label: node.label,
      x: node.getPosition().x,
      y: node.getPosition().y,
      inputFields: nodeData.inputFields || [],
      outputFields: nodeData.outputFields || [],
      preNodeIds: nodeData.preNodeIds || [],
      nextNodeIds: nodeData.nextNodeIds || [],
      desc: nodeData.desc || '',
      ports: node.getPorts ? node.getPorts() : []
    }
  })
}

async function onAddDag() {
  if (!(await confirmLeaveIfChanged())) return
  if (graph) {
    graph.clearCells()
  }
  const uuid = 'dag_' + Date.now()
  dagGraph.value = {
    id: uuid,
    name: '新建图_' + Date.now(),
    desc: '',
    nodes: [],
    edges: []
  }
  currentDagId.value = uuid
  console.log('[onAddDag] 新建图:', dagGraph.value)
  await saveDag()
  await fetchDag(uuid)
  nextTick(() => {
    const ul = document.querySelector('.dag-list-ul')
    if (ul) ul.scrollTop = ul.scrollHeight
  })
}

async function onSelectDag(id) {
  if (id === currentDagId.value) return
  if (!(await confirmLeaveIfChanged())) return
  console.log('[onSelectDag] 切换到图id:', id)
  await fetchDag(id)
  await fetchDagListAndSwitchToCurrent()
}

async function onDeleteDag(id) {
  if (!(await confirmLeaveIfChanged())) return
  isDeleting.value = true
  try {
    await ElMessageBox.confirm('确定要删除该图吗？删除后不可恢复！', '警告', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const res = await fetch(`/api/delete-dag?id=${id}`, { method: 'DELETE' })
    const result = await res.json()
    if (result.status === 'ok') {
      ElMessage.success('删除成功')
      await fetchDagList()
      if (dagList.value.length > 0) {
        await fetchDag(dagList.value[0].id)
      } else {
        await onAddDag()
      }
    } else {
      ElMessage.error('删除失败')
    }
  } catch (e) {
    // 用户取消
  } finally {
    isDeleting.value = false
  }
}

onMounted(async () => {
  await fetchDagList()
  console.log('[onMounted] 初始dagList:', dagList.value)
  if (dagList.value.length > 0) {
    await fetchDag(dagList.value[0].id)
    currentDagId.value = dagList.value[0].id
    console.log('[onMounted] 加载第一个图:', currentDagId.value)
  } else {
    await onAddDag()
    console.log('[onMounted] 没有图，自动新建')
  }
})

function startEditDagName(item) {
  editingDagId.value = item.id
  editingDagName.value = item.name
  nextTick(() => {
    const input = document.querySelector('.dag-list-edit-input')
    if (input) input.focus()
  })
}

async function saveEditDagName(item) {
  if (!editingDagName.value.trim() || editingDagName.value === item.name) {
    editingDagId.value = null
    return
  }
  // 先退出编辑状态
  const id = editingDagId.value
  editingDagId.value = null
  isSaving.value = true
  // 获取该图的完整数据
  let graphData = dagGraph.value
  if (item.id !== dagGraph.value.id) {
    try {
      const res = await fetch(`/api/load-dag?id=${item.id}`)
      const dag = await res.json()
      graphData = dag && dag.data ? JSON.parse(dag.data) : {}
    } catch {
      graphData = {}
    }
  }
  graphData.name = editingDagName.value.trim()
  const saveData = {
    id: item.id,
    name: editingDagName.value.trim(),
    data: JSON.stringify(graphData)
  }
  try {
    await fetch('/api/save-dag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(saveData)
    })
    await fetchDagList()
  } catch (e) {}
  isSaving.value = false
}

function openDagListPanel() { showDagListPanel.value = true }
function closeDagListPanel() { showDagListPanel.value = false }
function toggleDagListPanel() { showDagListPanel.value = !showDagListPanel.value }

// 点击空白处收起
onMounted(() => {
  document.addEventListener('click', handleGlobalClick)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleGlobalClick)
})
function handleGlobalClick(e) {
  const panel = document.querySelector('.dag-list-panel')
  const btn = document.querySelector('.dag-list-float-btn')
  if (showDagListPanel.value && panel && !panel.contains(e.target) && btn && !btn.contains(e.target)) {
    showDagListPanel.value = false
  }
}

function exportDagAsJson() {
  if (!dagGraph.value || !dagGraph.value.id) return
  const data = JSON.stringify(dagGraph.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${dagGraph.value.name || 'dag'}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function onImportDagClick() {
  if (importInputRef.value) importInputRef.value.click()
}

async function onImportDagFile(e) {
  const file = e.target.files[0]
  if (!file) return
  // 弹窗确认
  try {
    await ElMessageBox.confirm(
      '当前图内容将被导入的文件覆盖，是否继续？',
      '导入确认',
      {
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    e.target.value = ''
    return // 用户取消
  }
  const reader = new FileReader()
  reader.onload = async (evt) => {
    try {
      const data = JSON.parse(evt.target.result)
      // 只覆盖nodes和edges，保留当前id和name
      if (!data.nodes || !Array.isArray(data.nodes)) throw new Error('无效的DAG文件')
      if (graph) graph.clearCells()
      dagGraph.value.nodes = data.nodes
      dagGraph.value.edges = data.edges || []
      // 渲染节点和连线（复用fetchDag渲染部分）
      if (graph && dagGraph.value.nodes && dagGraph.value.nodes.length > 0) {
        dagGraph.value.nodes.forEach(node => {
          let ports = node.ports
          if (!ports || !ports.items || ports.items.length !== 32) {
            ports = {
              groups: {
                top: {
                  position: { name: 'top', args: { dx: 0 } },
                  attrs: {
                    circle: {
                      r: 2.5,
                      magnet: true,
                      stroke: '#409EFF',
                      strokeWidth: 1,
                      fill: '#fff',
                      style: {
                        pointerEvents: 'all',
                        opacity: 0.3,
                        transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                      }
                    }
                  }
                },
                right: {
                  position: { name: 'right', args: { dy: 0 } },
                  attrs: {
                    circle: {
                      r: 2.5,
                      magnet: true,
                      stroke: '#409EFF',
                      strokeWidth: 1,
                      fill: '#fff',
                      style: {
                        pointerEvents: 'all',
                        opacity: 0.3,
                        transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                      }
                    }
                  }
                },
                bottom: {
                  position: { name: 'bottom', args: { dx: 0 } },
                  attrs: {
                    circle: {
                      r: 2.5,
                      magnet: true,
                      stroke: '#409EFF',
                      strokeWidth: 1,
                      fill: '#fff',
                      style: {
                        pointerEvents: 'all',
                        opacity: 0.3,
                        transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                      }
                    }
                  }
                },
                left: {
                  position: { name: 'left', args: { dy: 0 } },
                  attrs: {
                    circle: {
                      r: 2.5,
                      magnet: true,
                      stroke: '#409EFF',
                      strokeWidth: 1,
                      fill: '#fff',
                      style: {
                        pointerEvents: 'all',
                        opacity: 0.3,
                        transition: 'opacity 0.2s, stroke 0.2s, fill 0.2s',
                      }
                    }
                  }
                }
              },
              items: generatePorts(node.id)
            }
          }
          graph.addNode({
            id: node.id,
            x: typeof node.x === 'number' ? node.x : Math.random() * 600,
            y: typeof node.y === 'number' ? node.y : Math.random() * 400,
            width: 200,
            height: 66,
            label: node.label,
            attrs: {
              body: {
                stroke: '#5F95FF',
                strokeWidth: 1,
                fill: '#fff',
                rx: 12,
                ry: 12,
                filter: 'drop-shadow(0 2px 8px #e6f7ff)',
              },
              label: {
                fontSize: 16,
                fill: '#222',
                fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
                fontWeight: 500,
              }
            },
            data: {
              label: node.label,
            },
            ports
          })
        })
        graph.getNodes().forEach(node => {
          node.getPorts().forEach(port => {
            node.setPortProp(port.id, 'attrs/circle/style/display', isEditMode.value ? '' : 'none')
          })
        })
        if (dagGraph.value.edges && dagGraph.value.edges.length > 0) {
          dagGraph.value.edges.forEach(edge => {
            const sourceNode = graph.getCellById(edge.source)
            const targetNode = graph.getCellById(edge.target)
            const sourcePortExists = sourceNode && sourceNode.getPorts().some(p => p.id === edge.sourcePort)
            const targetPortExists = targetNode && targetNode.getPorts().some(p => p.id === edge.targetPort)
            if (sourceNode && targetNode && sourcePortExists && targetPortExists) {
              graph.addEdge({
                source: { cell: edge.source, port: edge.sourcePort },
                target: { cell: edge.target, port: edge.targetPort },
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
            }
          })
        }
      }
      ElMessage.success('导入成功！')
    } catch (err) {
      ElMessage.error('导入失败：文件格式错误')
    }
  }
  reader.readAsText(file)
  e.target.value = ''
}

// 跳出当前图的操作前判断
async function confirmLeaveIfChanged() {
  if (isEditMode.value && is_change.value) {
    try {
      await ElMessageBox.confirm(
        '当前图还未保存，是否离开？',
        '未保存提示',
        {
          confirmButtonText: '离开',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
      return true
    } catch {
      return false
    }
  }
  return true
}

// 刷新/关闭浏览器前判断
window.addEventListener('beforeunload', (e) => {
  if (isEditMode.value && is_change.value) {
    e.preventDefault()
    e.returnValue = ''
    return ''
  }
})
</script>

<style>
.dag-editor-full {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}
.dag-mode-switch {
  position: absolute;
  top: 16px;
  right: 32px;
  z-index: 30;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 2px 8px #e6f7ff;
  padding: 6px 18px 6px 18px;
  display: flex;
  align-items: center;
}
.dag-mode-switch .el-switch {
  --el-switch-on-color: #409eff;
  --el-switch-off-color: #e0e0e0;
  border-radius: 16px;
  box-shadow: 0 1px 4px #e6f7ff;
  height: 28px;
  min-width: 60px;
}
.dag-graph-container {
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
  border: 1px solid #eee;
  border-radius: 14px;
  box-shadow: 0 4px 24px #e6f7ff;
  background: #fcfdff;
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
  border-radius: 0 0 12px 12px;
}
.node-edit-input {
  font-size: 16px;
  padding: 6px 16px;
  border: 1px solid #5F95FF;
  border-radius: 8px;
  outline: none;
  min-width: 120px;
  max-width: 320px;
  background: #fff;
  box-shadow: 0 1px 4px #f0f1f3;
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
  padding: 18px 32px 18px 32px;
  background: #fafdff;
  border-top: 1px solid #eee;
  box-sizing: border-box;
  border-radius: 0 0 16px 16px;
  box-shadow: 0 2px 8px #e6f7ff;
  margin-bottom: 8px;
}
.node-desc-text {
  font-size: 15px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
}
.node-desc-input .el-textarea__inner {
  font-size: 15px;
  min-height: 40px !important;
  background: #fff;
  border-radius: 10px;
  border: 1.5px solid #e0e0e0;
  box-shadow: 0 1px 6px #e6f7ff;
  transition: border 0.2s;
  padding: 10px 16px;
}
.node-desc-input .el-textarea__inner:focus {
  border: 1.5px solid #409eff;
  background: #fafdff;
}
.dag-search-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px 0 0 0;
  background: #fff;
  z-index: 11;
  box-shadow: 0 2px 8px #f0f1f3;
  border-radius: 0 0 14px 14px;
}
.search-input {
  font-size: 15px;
  border-radius: 10px;
  box-shadow: 0 1px 6px #e6f7ff;
  background: #fafdff;
  border: 1.5px solid #e0e0e0;
  transition: border 0.2s;
  height: 36px;
  padding-left: 12px;
}
.search-input input::placeholder {
  color: #bfcbd9;
  font-size: 15px;
}
.add-node-menu {
  position: fixed;
  z-index: 1000;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  box-shadow: 0 4px 16px #e6f7ff;
  min-width: 120px;
  padding: 4px 0;
}
.add-node-menu-item {
  padding: 10px 22px;
  cursor: pointer;
  font-size: 15px;
  color: #333;
  transition: background 0.2s, color 0.2s;
  border-radius: 6px;
}
.add-node-menu-item:hover, .node-menu-item:hover {
  background: #f0faff;
  color: #1890ff;
}
.node-menu {
  position: fixed;
  z-index: 1001;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  box-shadow: 0 4px 16px #e6f7ff;
  min-width: 120px;
  padding: 4px 0;
}
.node-menu-item {
  padding: 10px 22px;
  cursor: pointer;
  font-size: 15px;
  color: #333;
  transition: background 0.2s, color 0.2s;
  border-radius: 6px;
}
.node-menu-delete {
  color: #f56c6c;
  font-weight: bold;
}
.dag-list-float-btn {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 54px;
  height: 180px;
  background: #fafdff;
  border-radius: 0 18px 18px 0;
  box-shadow: 0 4px 16px #e6f7ff;
  border: 2.5px solid #409eff;
  color: #409eff;
  font-size: 28px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 30;
  user-select: none;
  transition: background 0.2s, color 0.2s, border 0.2s, box-shadow 0.2s;
  letter-spacing: 2px;
}
.dag-list-float-btn span {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.1;
}
.dag-list-float-btn:hover {
  background: #409eff;
  color: #fff;
  border: 2.5px solid #409eff;
  box-shadow: 0 6px 24px #e6f7ff;
}
.dag-list-panel {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) translateX(-100%);
  transition: transform 0.35s cubic-bezier(.4,1.3,.6,1);
  width: 180px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px #e6f7ff;
  padding: 18px 10px 18px 10px;
  z-index: 40;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  min-height: 400px;
}
.dag-list-panel.show {
  transform: translateY(-50%) translateX(0);
}
.dag-list-title {
  font-size: 18px;
  font-weight: bold;
  color: #f56c6c;
  margin-bottom: 12px;
  text-align: center;
}
.dag-list-ul {
  list-style: none;
  padding: 0;
  margin: 0 0 12px 0;
  max-height: 500px;
  overflow-y: auto;
}
.dag-list-item {
  position: relative;
  padding: 10px 12px 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  font-size: 15px;
  background: #f8fafc;
  box-shadow: 0 1px 4px #e6f7ff;
  border: 1.5px solid #f0f1f3;
  transition: background 0.2s, color 0.2s, border 0.2s;
  color: #333;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-height: 48px;
}
.dag-list-item-main {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.dag-list-item-title {
  font-weight: bold;
  font-size: 16px;
  color: #409eff;
  margin-bottom: 2px;
}
.dag-list-item-id {
  font-size: 12px;
  color: #bfcbd9;
  word-break: break-all;
}
.dag-list-item.active,
.dag-list-item:hover {
  background: #e6f7ff;
  border: 1.5px solid #409eff;
  color: #1890ff;
}
.dag-list-bottom-bar {
  width: 100%;
  margin-top: 8px;
  padding-bottom: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.dag-list-divider {
  width: 90%;
  height: 1.5px;
  background: linear-gradient(90deg, #f0f1f3 0%, #e6f7ff 100%);
  border-radius: 1px;
  margin-bottom: 12px;
}
.dag-list-add-btn-beauty {
  width: 92%;
  height: 40px;
  border-radius: 20px;
  font-size: 16px;
  font-weight: bold;
  background: #fff;
  color: #409eff;
  border: 1.5px solid #409eff;
  box-shadow: 0 2px 8px #e6f7ff;
  transition: background 0.2s, color 0.2s, border 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  margin-bottom: 2px;
}
.dag-list-add-btn-beauty:hover {
  background: #409eff;
  color: #fff;
  border: 1.5px solid #409eff;
}
.dag-save-btn {
  min-width: 80px;
}
.dag-list-delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0.85;
  z-index: 2;
  transition: opacity 0.2s;
}
.dag-list-delete-btn:hover {
  opacity: 1;
}
.dag-list-plus-bar {
  display: none !important;
}
.dag-list-add-item {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  background: #f8fafc;
  border-radius: 8px;
  box-shadow: 0 1px 4px #e6f7ff;
  border: 1.5px dashed #bfcbd9;
  margin-bottom: 8px;
  transition: background 0.2s, border 0.2s;
}
.dag-list-add-item:hover {
  background: #e6f7ff;
  border: 1.5px solid #409eff;
}
.dag-list-add-main {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dag-list-add-plus {
  font-size: 26px;
  color: #409eff;
  font-weight: bold;
}
.dag-ops-tip {
  position: absolute;
  top: 60px;
  left: 12px;
  font-size: 14px;
  color: #888;
  line-height: 1.7;
  background: transparent;
  border-radius: 8px;
  padding: 10px 18px 10px 14px;
  z-index: 20;
  pointer-events: none;
  user-select: text;
  max-width: 340px;
  min-width: 220px;
}
.ops-tip-key {
  font-weight: bold;
  color: #409eff;
  margin-right: 2px;
  letter-spacing: 0.5px;
}
</style>

<style>
.el-dialog__wrapper {
  display: flex !important;
  align-items: center;
  justify-content: center;
}
.el-dialog {
  margin: 0 !important;
}
</style>

<style scoped>
/* 删除.ai-chat-panel及相关样式 */
.dag-toolbar-bar {
  width: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-radius: 0 0 14px 14px;
  box-shadow: 0 2px 8px #f0f1f3;
  padding: 0 32px 0 0;
  min-height: 64px;
  margin-bottom: 0;
  z-index: 11;
}
.dag-search-bar {
  display: flex;
  align-items: center;
  padding: 0;
  background: none;
  box-shadow: none;
  border-radius: 0;
  margin-bottom: 0;
}
.dag-toolbar-group {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 2px 8px #e6f7ff;
  padding: 4px 12px 4px 12px;
  gap: 12px;
  height: 40px;
}
.dag-save-btn-beauty {
  min-width: 72px;
  height: 32px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 8px;
  box-shadow: 0 1px 4px #e6f7ff;
  letter-spacing: 1px;
  padding: 0 16px;
  line-height: 32px;
}
.dag-export-btn-beauty {
  min-width: 90px;
  height: 32px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
  box-shadow: 0 1px 4px #e6f7ff;
  letter-spacing: 1px;
  padding: 0 16px;
  line-height: 32px;
  margin-left: 4px;
}
.dag-import-btn-beauty {
  min-width: 90px;
  height: 32px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
  box-shadow: 0 1px 4px #e6f7ff;
  letter-spacing: 1px;
  padding: 0 16px;
  line-height: 32px;
  margin-left: 4px;
}
.dag-edit-switch-scale {
  display: flex;
  align-items: center;
  transform: scale(1.25);
  transform-origin: left center;
  min-width: 110px;
}
.dag-edit-switch {
  margin-left: 4px;
  --el-switch-on-color: #409eff;
  --el-switch-off-color: #e0e0e0;
  border-radius: 18px;
  box-shadow: 0 1px 4px #e6f7ff;
  min-width: 90px;
}
::v-deep(.dag-edit-switch .el-switch) {
  transform: scale(1.25);
}
::v-deep(.dag-edit-switch .el-switch__label) {
  font-size: 16px !important;
  font-weight: 600;
}
</style>

<style>
.dag-edit-switch .el-switch {
  transform: scale(1.25) !important;
}
.dag-edit-switch .el-switch__label {
  font-size: 16px !important;
  font-weight: 600;
}
</style> 