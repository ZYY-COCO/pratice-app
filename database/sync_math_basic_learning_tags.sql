-- Sync learning-analysis metadata for generated/math_basic_500.json imported rows.
-- Safe to rerun: rows are matched by exam_code, subject, module, submodule and stem.
update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 2x}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+3x)}{e^{4x}-1}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{5}-1}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{5}{x}\right)\) 的值。';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{1}{n}\right)^{3n}\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 2x-2x}{x^3}\) 的值。';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{3x^2+3}\) 的值。';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 2x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 6x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+4x}-1}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan 5x}{\sin 4x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 6x}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+1)^{2}\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+3x^2)\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{8}\)，则 \(y^{(3)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+45}\)，则在 \(x=1\) 处的微分 \(dy=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=x^{3}e^x\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(y=x^3+6x^2+x\) 的凹区间为？';

update public.questions
set skill_tags = ARRAY['拐点判断', '二阶导数', '符号变化']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '误把驻点当拐点', '坐标遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '拐点'
  and stem = '函数 \(y=x^3-9x^2+2\) 的拐点横坐标为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^2-8x+3\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(12-x)\) 在 \([0,12]\) 上的最大值为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{6x+1}{3x+2}\) 的水平渐近线为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{x+1}{x-7}\) 的竖直渐近线为？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(2x+1)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{3x^2}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin 7x\,dx\)。';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(5x+\frac{3}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^2}\sin t\,dt\)，则 \(F''(x)=\)？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^{4}7\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=2x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=4x\)、\(x=0\)、\(x=5\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^5\)，且 \(F(0)=0\)，则 \(F(1)=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{2}y\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(x^{2}y)\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(3,2)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((4,2)\) 处 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=5x+3y\)，且 \(f''(u)=2\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=5\) 确定，则在点 \((4,5,6)\) 处 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-4x-8y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{6}y^{6}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(x^{3}y)}\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+x)}{e^{4x}-1}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{2}-1}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{1}{x}\right)\) 的值。';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{3}{n}\right)^n\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 4x-4x}{x^3}\) 的值。';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{5x^2+3}\) 的值。';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 6x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 3x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+8x}-1}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan 3x}{\sin 2x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 2x}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+4)^{2}\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+4x^2)\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{6}\)，则 \(y^{(2)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+5}\)，则在 \(x=1\) 处的微分 \(dy=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=xe^x\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(y=x^3-12x\) 的极小点横坐标为？';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(y=x^3+9x^2+x\) 的凹区间为？';

update public.questions
set skill_tags = ARRAY['拐点判断', '二阶导数', '符号变化']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '误把驻点当拐点', '坐标遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '拐点'
  and stem = '函数 \(y=x^3-9x^2+2\) 的拐点横坐标为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^2-10x+1\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(8-x)\) 在 \([0,8]\) 上的最大值为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{2x+1}{2x+2}\) 的水平渐近线为？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x^{4}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(5x+0)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{4x^2}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin 9x\,dx\)。';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(x^{4}+\frac{3}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^3}\sin t\,dt\)，则 \(F''(x)=\)？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^{4}2\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=6x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=5x\)、\(x=0\)、\(x=5\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^4\)，且 \(F(0)=0\)，则 \(F(1)=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{3}y^{2}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(x^{3}y^{2})\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(2,3)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 45
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((3,4)\) 处 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 60
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=x+3y\)，且 \(f''(u)=1\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=0\) 确定，则在点 \((3,4,5)\) 处 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-2x-8y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{2}y^{2}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(x^{2}y)}\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+6x)}{e^{4x}-1}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{4}-1}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{5}{x}\right)\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{5}{n}\right)^{3n}\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin x-x}{x^3}\) 的值。';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{2x^2+3}\) 的值。';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 2x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 5x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+4x}-1}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan x}{\sin 6x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 6x}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+4x)}{e^{4x}-1}\) 的值。';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+2)^{2}\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+5x^2)\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{4}\)，则 \(y^{(4)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+21}\)，则在 \(x=1\) 处的微分 \(dy=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=x^{4}e^x\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{x+1}{x-7}\) 的竖直渐近线为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(y=x^3-48x\) 的极小点横坐标为？';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(y=x^3+12x^2+x\) 的凹区间为？';

update public.questions
set skill_tags = ARRAY['拐点判断', '二阶导数', '符号变化']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '误把驻点当拐点', '坐标遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '拐点'
  and stem = '函数 \(y=x^3-9x^2+2\) 的拐点横坐标为？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^2-12x+4\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(4-x)\) 在 \([0,4]\) 上的最大值为？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x^{7}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(8x+5)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{5x^2}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin x\,dx\)。';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(2x^{3}+\frac{4}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^4}\sin t\,dt\)，则 \(F''(x)=\)？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^{5}5\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=3x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=x\)、\(x=0\)、\(x=1\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^3\)，且 \(F(0)=0\)，则 \(F(1)=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{4}y^{4}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(x^{4}y^{2})\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((2,1)\) 处 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=2x+4y\)，且 \(f''(u)=4\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=-3\) 确定，则在点 \((2,3,4)\) 处 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-12x-6y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{3}y^{2}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(xy)}\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{6}-1}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{1}{x}\right)\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{2}{n}\right)^n\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 3x-3x}{x^3}\) 的值。';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{4x^2+3}\) 的值。';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 6x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 2x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+8x}-1}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan 6x}{\sin 4x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 2x}{x}\) 的值。（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+2x)}{e^{4x}-1}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{3}-1}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+5)^{2}\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+6x^2)\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{7}\)，则 \(y^{(3)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+45}\)，则在 \(x=1\) 处的微分 \(dy=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=x^{2}e^x\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{4x+1}{x+2}\) 的水平渐近线为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{x+1}{x-7}\) 的竖直渐近线为？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(y=x^3-108x\) 的极小点横坐标为？';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(y=x^3+15x^2+x\) 的凹区间为？';

update public.questions
set skill_tags = ARRAY['拐点判断', '二阶导数', '符号变化']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '误把驻点当拐点', '坐标遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '拐点'
  and stem = '函数 \(y=x^3-9x^2+2\) 的拐点横坐标为？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^2-14x+2\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x^{2}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(3x+4)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{x^2}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin 3x\,dx\)。';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(3x^{2}+\frac{4}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^5}\sin t\,dt\)，则 \(F''(x)=\)？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^{5}8\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=7x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=2x\)、\(x=0\)、\(x=1\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^2\)，且 \(F(0)=0\)，则 \(F(1)=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{5}y\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(x^{5}y^{3})\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(4,2)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((1,3)\) 处 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=3x+4y\)，且 \(f''(u)=3\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=0\) 确定，则在点 \((5,12,13)\) 处 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-10x-6y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 90
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{4}y^{3}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(x^{4}y)}\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{5}{x}\right)\) 的值。（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{4}{n}\right)^{3n}\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 5x-5x}{x^3}\) 的值。';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{x^2+3}\) 的值。';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 2x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 4x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+4x}-1}{x}\) 的值。（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan 4x}{\sin 2x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 6x}{x}\) 的值。（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+7x)}{e^{4x}-1}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{5}-1}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{1}{x}\right)\) 的值。（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+3)^{2}\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+7x^2)\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{5}\)，则 \(y^{(2)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+5}\)，则在 \(x=1\) 处的微分 \(dy=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=x^{5}e^x\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(10-x)\) 在 \([0,10]\) 上的最大值为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{6x+1}{5x+2}\) 的水平渐近线为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{x+1}{x-7}\) 的竖直渐近线为？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(y=x^3-12x\) 的极小点横坐标为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(y=x^3+18x^2+x\) 的凹区间为？';

update public.questions
set skill_tags = ARRAY['拐点判断', '二阶导数', '符号变化']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '误把驻点当拐点', '坐标遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '拐点'
  and stem = '函数 \(y=x^3-9x^2+2\) 的拐点横坐标为？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 75
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x^{5}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(6x+3)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 150
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{2x^2}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin 5x\,dx\)。';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(4x+\frac{5}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^6}\sin t\,dt\)，则 \(F''(x)=\)？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_03\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=4x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=3x\)、\(x=0\)、\(x=2\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^1\)，且 \(F(0)=0\)，则 \(F(1)=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{6}y^{3}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(xy^{3})\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(3,4)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((4,4)\) 处 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=4x+5y\)，且 \(f''(u)=2\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=5\) 确定，则在点 \((4,5,6)\) 处 \(\frac{\partial z}{\partial x}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-8x-4y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{5}y^{3}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(x^{3}y)}\)，则 \(dz=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{1}{n}\right)^n\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 2x-2x}{x^3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{3x^2+3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 6x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 6x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+8x}-1}{x}\) 的值。（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan 2x}{\sin 6x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 2x}{x}\) 的值。（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+5x)}{e^{4x}-1}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{2}-1}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{5}{x}\right)\) 的值。（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{3}{n}\right)^{3n}\) 的值。';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+1)^{2}\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+x^2)\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{8}\)，则 \(y^{(4)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+21}\)，则在 \(x=1\) 处的微分 \(dy=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=x^{3}e^x\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^2-2x+0\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(6-x)\) 在 \([0,6]\) 上的最大值为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{2x+1}{4x+2}\) 的水平渐近线为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{x+1}{x-7}\) 的竖直渐近线为？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(y=x^3-48x\) 的极小点横坐标为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(y=x^3+21x^2+x\) 的凹区间为？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x^{8}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(x+2)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 150
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{3x^2}\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin 7x\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(5x^{4}+\frac{5}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^2}\sin t\,dt\)，则 \(F''(x)=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_06\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=8x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=4x\)、\(x=0\)、\(x=2\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^6\)，且 \(F(0)=0\)，则 \(F(1)=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{2}y^{4}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(x^{2}y^{4})\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(2,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((3,2)\) 处 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=5x+5y\)，且 \(f''(u)=5\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=0\) 确定，则在点 \((3,4,5)\) 处 \(\frac{\partial z}{\partial x}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-6x-4y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{6}y^{4}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(x^{2}y)}\)，则 \(dz=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 4x-4x}{x^3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{5x^2+3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 2x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 3x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+4x}-1}{x}\) 的值。（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan 7x}{\sin 4x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 6x}{x}\) 的值。（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+3x)}{e^{4x}-1}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{4}-1}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{1}{x}\right)\) 的值。（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{5}{n}\right)^n\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin x-x}{x^3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+4)^{2}\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+2x^2)\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{6}\)，则 \(y^{(3)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+45}\)，则在 \(x=1\) 处的微分 \(dy=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=xe^x\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['拐点判断', '二阶导数', '符号变化']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '误把驻点当拐点', '坐标遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '拐点'
  and stem = '函数 \(y=x^3-9x^2+2\) 的拐点横坐标为？（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^2-4x+3\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(12-x)\) 在 \([0,12]\) 上的最大值为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{4x+1}{3x+2}\) 的水平渐近线为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{x+1}{x-7}\) 的竖直渐近线为？（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(y=x^3-108x\) 的极小点横坐标为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x^{3}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(4x+1)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 150
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{4x^2}\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin 9x\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(x^{3}+\frac{1}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^3}\sin t\,dt\)，则 \(F''(x)=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^{2}1\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=5x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=5x\)、\(x=0\)、\(x=3\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^5\)，且 \(F(0)=0\)，则 \(F(1)=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{3}y^{2}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(x^{3}y^{4})\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,3)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((2,3)\) 处 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=x+y\)，且 \(f''(u)=4\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=-3\) 确定，则在点 \((2,3,4)\) 处 \(\frac{\partial z}{\partial x}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-4x-2y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{2}y^{4}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(xy)}\)，则 \(dz=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{2x^2+3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 6x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 5x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+8x}-1}{x}\) 的值。（按常规微积分方法计算。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan 5x}{\sin 2x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 2x}{x}\) 的值。（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（选出与计算结果一致的一项。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+x)}{e^{4x}-1}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{6}-1}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{5}{x}\right)\) 的值。（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{2}{n}\right)^{3n}\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 3x-3x}{x^3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{4x^2+3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+2)^{2}\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+3x^2)\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{4}\)，则 \(y^{(2)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+5}\)，则在 \(x=1\) 处的微分 \(dy=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=x^{4}e^x\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(y=x^3+3x^2+x\) 的凹区间为？';

update public.questions
set skill_tags = ARRAY['拐点判断', '二阶导数', '符号变化']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '误把驻点当拐点', '坐标遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '拐点'
  and stem = '函数 \(y=x^3-9x^2+2\) 的拐点横坐标为？（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^2-6x+1\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(8-x)\) 在 \([0,8]\) 上的最大值为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{6x+1}{2x+2}\) 的水平渐近线为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{x+1}{x-7}\) 的竖直渐近线为？（计算过程不需要展开到高阶项以外。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(y=x^3-12x\) 的极小点横坐标为？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x^{6}\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(7x+0)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 150
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{5x^2}\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin x\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(2x^{2}+\frac{1}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^4}\sin t\,dt\)，则 \(F''(x)=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^{2}4\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=2x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=x\)、\(x=0\)、\(x=3\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^4\)，且 \(F(0)=0\)，则 \(F(1)=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{4}y^{3}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(x^{4}y^{5})\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(4,4)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 135
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((1,1)\) 处 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 165
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=2x+y\)，且 \(f''(u)=3\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=0\) 确定，则在点 \((5,12,13)\) 处 \(\frac{\partial z}{\partial x}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-2x-2y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{3}y^{5}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(x^{4}y)}\)，则 \(dz=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 2x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 2x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+4x}-1}{x}\) 的值。（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan 3x}{\sin 6x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 6x}{x}\) 的值。（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{1-\cos 2x}{x^2}\) 的值。（注意保留必要系数。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+6x)}{e^{4x}-1}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{(1+4x)^{3}-1}{x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['对数化极限', '重要极限', '等价无穷小']::text[],
    mistake_tags = ARRAY['忽略对数化', '忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}x\ln\left(1+\frac{1}{x}\right)\) 的值。（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{n\to\infty}\left(1+\frac{4}{n}\right)^n\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 5x-5x}{x^3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['无穷远处极限', '最高次项比较', '有理函数极限']::text[],
    mistake_tags = ARRAY['最高次项判断错误', '系数比写反', '忽略低阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}\frac{3x^2+4x+1}{x^2+3}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['连续性判断', '左右极限', '函数值匹配']::text[],
    mistake_tags = ARRAY['左右极限混淆', '漏用函数值', '条件缺失']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\sin 6x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+5)^{2}\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（选出与计算结果一致的一项。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln(1+4x^2)\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '曲线 \(x^2+y^2=625\) 上点 \((7,24)\) 处的 \(\frac{dy}{dx}=\)？（选出与计算结果一致的一项。）';

update public.questions
set skill_tags = ARRAY['高阶导数', '幂函数求导', '阶乘系数']::text[],
    mistake_tags = ARRAY['高阶导数阶数错误', '系数计算错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=x^{7}\)，则 \(y^{(4)}(1)=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '微分'
  and stem = '设 \(y=\sqrt{4x+21}\)，则在 \(x=1\) 处的微分 \(dy=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\tan 7x\)，则 \(y''|_{x=0}=\)？（选出与计算结果一致的一项。）';

update public.questions
set skill_tags = ARRAY['乘积求导', '导数计算', '函数值代入']::text[],
    mistake_tags = ARRAY['乘积求导漏项', '代入点错误', '符号错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=x^{2}e^x\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(y=x^3+6x^2+x\) 的凹区间为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['拐点判断', '二阶导数', '符号变化']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '误把驻点当拐点', '坐标遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '拐点'
  and stem = '函数 \(y=x^3-9x^2+2\) 的拐点横坐标为？（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^2-8x+4\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(4-x)\) 在 \([0,4]\) 上的最大值为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{2x+1}{x+2}\) 的水平渐近线为？';

update public.questions
set skill_tags = ARRAY['渐近线判断', '有理函数分析', '极限思想']::text[],
    mistake_tags = ARRAY['水平渐近线系数比写反', '竖直渐近线位置错误', '分母零点遗漏']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '渐近线'
  and stem = '函数 \(y=\frac{x+1}{x-7}\) 的竖直渐近线为？（答案以化简后的形式为准。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(2x+5)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 255
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{x^2}\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin 3x\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['不定积分', '原函数', '基本积分公式']::text[],
    mistake_tags = ARRAY['漏写积分常数', '公式套用错误', '系数处理错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '原函数'
  and stem = '求不定积分 \(\int(3x+\frac{2}{x})\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_0^{x^5}\sin t\,dt\)，则 \(F''(x)=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^{3}7\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=6x\) 与 \(y=x^2\) 在第一象限围成图形的面积为？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=2x\)、\(x=0\)、\(x=4\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^1 xe^x\,dx\)。（选出与计算结果一致的一项。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '若 \(F''(x)=x^3\)，且 \(F(0)=0\)，则 \(F(1)=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{5}y\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(x^{5}y^{5})\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(3,2)}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=x^2y+y^2\)，则在点 \((4,2)\) 处 \(dz=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u)\)，\(u=3x+2y\)，且 \(f''(u)=1\)，则 \(\frac{\partial z}{\partial x}=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x+y\)，\(v=xy\)，且 \(f_u=A\)，\(f_v=B\)，则 \(\frac{\partial z}{\partial x}=\)？（选出与计算结果一致的一项。）';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=5\) 确定，则在点 \((4,5,6)\) 处 \(\frac{\partial z}{\partial x}=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2-12x-12y\) 的极小值为？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2-y^2\) 在 \((0,0)\) 处的极值情况是？（选出与计算结果一致的一项。）';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^{4}y^{5}\)，则 \(\left.\frac{\partial^2 z}{\partial x\partial y}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(x^{3}y)}\)，则 \(dz=\)？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1}{\sin 4x}\) 的值。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+8x}-1}{x}\) 的值。（结果用标准形式表示。）';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\tan x}{\sin 4x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin 2x}{x}\) 的值。（只需判断最终结果。）';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\cos x-e^{3x}}{\tan 2x}\) 的值。';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\ln(1+5x)-\sin2x}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sqrt{1+6x}-\sqrt{1+2x}}{x}\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{e^{4x}-1-4x}{x^2}\) 的值。';

update public.questions
set skill_tags = ARRAY['简单泰勒展开', '等价无穷小', '高阶无穷小比较']::text[],
    mistake_tags = ARRAY['展开阶数不足', '符号错误', '忽略高阶项']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}\frac{\sin2x-2x\cos3x}{x^3}\) 的值。';

update public.questions
set skill_tags = ARRAY['等价无穷小', '极限计算']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to\infty}(\sqrt{x^2+8x}-x)\) 的值。';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '连续'
  and stem = '设 \(f(x)=\begin{cases}\frac{\ln(1+3x)-\sin x}{x},&x\ne0,\\ a,&x=0.\end{cases}\) 若 \(f(x)\) 在 \(x=0\) 连续，则 \(a=\)？';

update public.questions
set skill_tags = ARRAY['洛必达法则', '未定式极限', '导数化简']::text[],
    mistake_tags = ARRAY['洛必达条件误判', '求导后符号错误', '公式套用错误']::text[],
    solution_type = 'lhopital',
    estimated_time_sec = 375
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '洛必达法则'
  and stem = '求极限 \(\lim_{x\to1}\frac{\ln x}{x-1}\) 的值。';

update public.questions
set skill_tags = ARRAY['重要极限', '等价无穷小', '极限公式识别']::text[],
    mistake_tags = ARRAY['忘记等价无穷小', '指数倍数处理错误', '公式套用错误']::text[],
    solution_type = 'algebra_transform',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极限'
  and stem = '求极限 \(\lim_{x\to0}(1+2x)^{1/x}\) 的值。';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=(x^2+3)^{2}\)，则 \(y''|_{x=1}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{2x}\cos x\)，则 \(y''|_{x=0}=\)？（注意保留必要系数。）';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(f(1)=1\)，\(f''(1)=3\)，\(f''''(1)=2\)，若 \(g(x)=f(f(x))\)，则 \(g''''(1)=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '两边求导', '切线斜率']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '链式法则漏乘', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '函数 \(y\) 由方程 \(x^2-(x+2)e^y=0\) 确定，求 \(\left.\frac{dy}{dx}\right|_{x=1}\)。';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\ln\sqrt{1+x^2}\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '高阶导数'
  and stem = '设 \(y=(\ln x)^3\)，则 \(y''''|_{x=e}=\)？';

update public.questions
set skill_tags = ARRAY['导数公式', '函数值代入']::text[],
    mistake_tags = ARRAY['公式套用错误', '代入点错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=\frac{x+1}{x^2+1}\)，则 \(y''|_{x=1}=\)？';

update public.questions
set skill_tags = ARRAY['复合函数求导', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '内层导数遗漏', '符号错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '导数'
  and stem = '设 \(y=e^{x^2}\ln(1+x)\)，则 \(y''|_{x=0}=\)？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(y=x^3-48x\) 的极小点横坐标为？（请选择正确结果。）';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 270
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(y=x^2-2x+1\) 的单调递减区间为？（选出与计算结果一致的一项。）';

update public.questions
set skill_tags = ARRAY['单调性判断', '一阶导数符号', '区间分析']::text[],
    mistake_tags = ARRAY['导数符号判断错误', '区间写反', '临界点遗漏']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '单调性'
  and stem = '函数 \(f(x)=x^3-6x^2+9x+1\) 的单调递增区间为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x^3-6x^2+9x+1\) 的极小点横坐标为？';

update public.questions
set skill_tags = ARRAY['凹凸性判断', '二阶导数', '区间判断']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '区间端点处理错误', '符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '凹凸性'
  and stem = '函数 \(f(x)=x^4-4x^3\) 的凹区间为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x(4-x)^2\) 在 \([0,4]\) 上的最大值为？';

update public.questions
set skill_tags = ARRAY['极值判定', '最值计算', '驻点分析']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '端点值遗漏', '驻点计算错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数微分学'
  and submodule = '极值与最值'
  and stem = '函数 \(f(x)=x+\frac{4}{x}\,(x>0)\) 的最小值为？';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1 x^{4}\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^1(5x+4)\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 255
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x e^{2x^2}\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算定积分 \(\int_0^\pi \sin 5x\,dx\)。（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 375
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^4\frac{\sin\sqrt{x}}{\sqrt{x}}\,dx\)。';

update public.questions
set skill_tags = ARRAY['换元积分', '定积分计算', '积分上下限转换']::text[],
    mistake_tags = ARRAY['换元后未改上下限', '微分替换错误', '系数遗漏']::text[],
    solution_type = 'substitution',
    estimated_time_sec = 375
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '换元积分'
  and stem = '计算定积分 \(\int_0^1 x\ln(1+x^2)\,dx\)。';

update public.questions
set skill_tags = ARRAY['变限定积分', '链式法则', '导数计算']::text[],
    mistake_tags = ARRAY['积分上限求导漏乘', '链式法则漏乘', '上下限处理错误']::text[],
    solution_type = 'derivative_chain_rule',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '变限定积分'
  and stem = '设 \(F(x)=\int_x^{x^2}\cos t\,dt\)，则 \(F''(0)=\)？';

update public.questions
set skill_tags = ARRAY['定积分几何应用', '面积计算', '上下函数判断']::text[],
    mistake_tags = ARRAY['上下函数判断错误', '积分上下限处理错误', '面积符号错误']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '由 \(y=\sqrt{x}\) 与 \(y=x\) 在 \([0,1]\) 上围成图形的面积为？';

update public.questions
set skill_tags = ARRAY['旋转体体积', '定积分几何应用', '平方积分']::text[],
    mistake_tags = ARRAY['旋转体公式套用错误', '积分上下限处理错误', '漏乘π']::text[],
    solution_type = 'geometric_application',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '几何应用'
  and stem = '曲线 \(y=\sqrt{x}\)、\(x=0\)、\(x=4\) 与 \(x\) 轴围成图形绕 \(x\) 轴旋转一周的体积为？';

update public.questions
set skill_tags = ARRAY['分部积分', '定积分计算', '乘积型积分']::text[],
    mistake_tags = ARRAY['分部积分公式套用错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '分部积分'
  and stem = '计算定积分 \(\int_0^{\pi/2}x\sin x\,dx\)。';

update public.questions
set skill_tags = ARRAY['定积分', '牛顿-莱布尼兹公式', '端点代入']::text[],
    mistake_tags = ARRAY['积分上下限处理错误', '端点代入错误', '符号错误']::text[],
    solution_type = 'definite_integral',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '一元函数积分学'
  and submodule = '定积分'
  and stem = '计算 \(\int_0^{3\pi}|\sin x|\,dx\)。';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=x^{6}y^{2}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(1,1)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=\ln(xy)\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['偏导数', '多元函数微分', '函数值代入']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '代入点错误', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 240
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '偏导数'
  and stem = '设 \(z=e^{xy}\)，则 \(\left.\frac{\partial z}{\partial x}\right|_{(2,3)}=\)？（结果化为最简形式。）';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '设 \(z=f(x,y)\)，\(f_x=A\)，\(f_y=B\)，则 \(d(\arctan z)=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '函数 \(u(x,y)\)、\(v(x,y)\) 由 \(x=2u+v\)，\(y=u-v\) 决定，则 \(u_x+v_x+u_y+v_y=\)？';

update public.questions
set skill_tags = ARRAY['多元链式法则', '复合函数求偏导', '偏导数']::text[],
    mistake_tags = ARRAY['链式法则漏乘', '偏导变量混淆', '中间变量遗漏']::text[],
    solution_type = 'multivariable_chain_rule',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '链导法则'
  and stem = '设 \(z=f(u,v)\)，\(u=x^2+y\)，\(v=x-y^2\)，且在所求点 \(f_u=2\)，\(f_v=-1\)。则在 \((1,1)\) 处 \(z_x=\)？';

update public.questions
set skill_tags = ARRAY['隐函数求导', '偏导数', '多元隐函数']::text[],
    mistake_tags = ARRAY['隐函数求导漏项', '偏导变量混淆', '符号错误']::text[],
    solution_type = 'implicit_differentiation',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '隐函数求导'
  and stem = '设 \(z=z(x,y)\) 由 \(x^2+y^2-z^2=5\) 确定，则在点 \((4,5,6)\) 处 \(z_x=\)？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+xy+y^2\) 在 \((0,0)\) 处的极值情况是？';

update public.questions
set skill_tags = ARRAY['二阶偏导数', '偏导顺序', '连续性条件']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '二阶偏导计算错误', '符号错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二阶偏导'
  and stem = '设 \(z=x^2y+\sin(xy)\)，则 \(\left.z_{xy}\right|_{(0,0)}=\)？';

update public.questions
set skill_tags = ARRAY['全微分', '偏导数', '微分表达式']::text[],
    mistake_tags = ARRAY['偏导变量混淆', '漏写dx或dy', '公式套用错误']::text[],
    solution_type = 'direct_formula',
    estimated_time_sec = 360
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '全微分'
  and stem = '在定义域内，设 \(z=\sqrt{\ln(xy^2)}\)，则 \(dz=\)？';

update public.questions
set skill_tags = ARRAY['二元函数极值', '驻点判断', '二阶判别式']::text[],
    mistake_tags = ARRAY['二阶导判断错误', '驻点遗漏', '判别式符号错误']::text[],
    solution_type = 'extremum_judgment',
    estimated_time_sec = 390
where exam_code = 'Z002'
  and subject = '数学基础'
  and module = '多元函数微分学'
  and submodule = '二元函数极值'
  and stem = '函数 \(f(x,y)=x^2+y^2+2x-4y+5\) 的极小值为？';
