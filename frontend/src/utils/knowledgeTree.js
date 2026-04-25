export const KNOWLEDGE_TREE = {
  中华文化: [
    {
      module: '中国哲学常识',
      description: '儒家、道家、墨家、法家与后代学派流变',
      submodules: ['儒家', '道家', '墨家', '法家', '后代学派流变', '古代宗教流变']
    },
    {
      module: '中国历史学常识',
      description: '职官、科举、礼俗、经济与近现代史学常识',
      submodules: ['古代职官与科举', '古代礼俗与称谓', '古代衣食住行', '古代军事战争', '古代经济发展', '古代图书文物', '近现代史学常识']
    },
    {
      module: '中国文学常识',
      description: '文体流变、作家作品与文学流派',
      submodules: ['文体流变', '代表作家及作品', '创作群体及文学流派', '文学总集', '民族史诗']
    },
    {
      module: '中国艺术常识',
      description: '书法、绘画、雕塑、建筑、音乐与戏剧',
      submodules: ['书法', '绘画', '雕塑', '建筑', '音乐', '戏剧', '民俗']
    },
    {
      module: '中国古代科技常识',
      description: '天文历法、农业水利、医学与科技发明',
      submodules: ['天文历法与算学', '地理舆图', '农业水利', '医学', '科技发明']
    }
  ],
  英语运用: [
    {
      module: '语言知识',
      description: '词汇、语法、语用',
      submodules: ['词汇', '语法', '语用']
    },
    {
      module: '阅读理解',
      description: '主旨、细节、推断、词义与结构题',
      submodules: ['阅读主旨题', '阅读细节题', '阅读推断题', '阅读词义题', '阅读结构题']
    }
  ],
  逻辑推理: [
    {
      module: '概念',
      description: '概念种类、关系、定义与划分',
      submodules: ['概念种类', '概念关系', '定义', '划分']
    },
    {
      module: '判断',
      description: '判断种类与判断关系',
      submodules: ['判断种类', '判断关系']
    },
    {
      module: '推理',
      description: '演绎、归纳、类比与综合推理',
      submodules: ['演绎推理', '归纳推理', '类比推理', '综合推理']
    },
    {
      module: '论证',
      description: '加强、削弱、解释与谬误识别',
      submodules: ['加强', '削弱', '解释', '谬误识别']
    }
  ],
  数学基础: [
    {
      module: '一元函数微分学',
      description: '极限、连续、导数、微分与函数性质',
      submodules: ['极限', '连续', '导数', '微分', '高阶导数', '洛必达法则', '单调性', '极值与最值', '凹凸性', '拐点', '渐近线']
    },
    {
      module: '一元函数积分学',
      description: '原函数、定积分与积分应用',
      submodules: ['原函数', '定积分', '变限定积分', '牛顿-莱布尼兹公式', '换元积分', '分部积分', '几何应用', '物理应用']
    },
    {
      module: '多元函数微分学',
      description: '偏导数、全微分、链导法则与极值',
      submodules: ['偏导数', '全微分', '二阶偏导', '链导法则', '隐函数求导', '二元函数极值']
    }
  ]
}

export function getSubjectTree(subject) {
  return KNOWLEDGE_TREE[subject] || []
}
