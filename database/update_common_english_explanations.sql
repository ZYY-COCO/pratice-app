-- Update detailed Chinese explanations for COMMON English language knowledge questions.
-- Safe to run after the questions have already been imported.
begin;

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（objections）。空格处应选择该项，核心理由是：objection 表示“反对意见”；objective 是“目标”。其余选项（B. objects；C. observations；D. objectives）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The plan was approved despite some minor ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（evaluate）。空格处应选择该项，核心理由是：evaluate 表示“评估、评价”，符合委员会审议方案的语境。其余选项（A. illustrate；C. imitate；D. estimate）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The committee will ______ the proposal before making a final decision.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（be finished）。空格处应选择该项，核心理由是：demand 等表示要求、命令、建议的动词后接 that 从句时，常用虚拟语气，即 should + 动词原形，should 可以省略。其余选项（A. was finished；B. is finished；C. finished）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The manager demanded that the report ______ before Friday.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（was）。空格处应选择该项，核心理由是：neither...nor...连接主语时，谓语遵循就近原则；teacher 为单数，故用 was。其余选项（B. were；C. are；D. have been）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Neither the students nor the teacher ______ aware of the change at that time.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（that）。空格处应选择该项，核心理由是：先行词被 all 修饰，定语从句中关系代词常用 that。其余选项（A. who；B. where；D. what）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'He gave me all the information ______ I needed.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（reliable）。空格处应选择该项，核心理由是：reliable data 表示“可靠数据”。其余选项（A. relative；B. relevantly；D. reluctant）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The speaker''s argument was persuasive because it was supported by ______ data.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（in）。空格处应选择该项，核心理由是：differ in sth. 表示“在某方面不同”，强调差异体现在某一具体方面。其余选项（A. with；B. by；C. from）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The two candidates differ ______ their views on education.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（volunteering）。空格处应选择该项，核心理由是：介词 by 后接动名词，表示“通过做某事”。其余选项（A. volunteer；C. volunteered；D. to volunteer）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'He insisted on realizing his dream by ______ as a teacher in a poor village.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 B（That''s all right. Thank you anyway.）。题干所问内容应选择该项，核心理由是：对方无法帮忙时，礼貌回应可用 Thank you anyway.其余选项（A. I don''t care.；C. You are welcome.；D. You must help me.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which response is appropriate after someone says, “I''m afraid I can''t help you today”?';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（adopted）。空格处应选择该项，核心理由是：adopt a method 表示“采用一种方法”；adapt 表示“适应、改编”。其余选项（B. admitted；C. adapted；D. adjusted）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new teaching method has been widely ______ by local schools.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（that）。空格处应选择该项，核心理由是：fact 后接同位语从句说明具体内容，用 that。其余选项（A. which；C. why；D. what）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The fact ______ he passed the exam surprised his friends.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（aptitude）。空格处应选择该项，核心理由是：aptitude for 表示“在某方面的天资、能力倾向”。其余选项（A. altitude；B. attitude；C. attribute）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The boy has a natural ______ for languages.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（raise）。空格处应选择该项，核心理由是：raise funds 是固定搭配，表示“筹集资金”。其余选项（A. rise；C. rouse；D. arise）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The charity campaign aims to ______ funds for rural schools.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（revise）。空格处应选择该项，核心理由是：revise 表示“修改、修订”，强调重新考虑后作出改进；reverse 表示“颠倒、反转”，语义不合。其余选项（A. review；B. reverse；C. reveal）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The committee decided to ______ the new policy after public criticism.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 C（Similarly）。题干所问内容应选择该项，核心理由是：Similarly 用于连接相似观点或情况。其余选项（A. Nevertheless；B. Despite；D. On the contrary）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which phrase best connects two similar ideas?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（How）。空格处应选择该项，核心理由是：How + 副词/形容词 + 主语 + 谓语，构成感叹句。其余选项（A. What；C. What a；D. How a）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '______ smartly dressed you are today!';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（warmly）。空格处应选择该项，核心理由是：respond warmly 表示“热烈回应”。其余选项（B. closely；C. nearly；D. barely）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The audience responded ______ to the speaker''s humorous examples.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（read）。空格处应选择该项，核心理由是：It is essential that... 从句常用 should do，should 可省略。其余选项（A. has read；C. reads；D. reading）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'It is essential that every student ______ the instructions carefully.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（Could you please help me check this sentence?）。题干所问内容应选择该项，核心理由是：Could you please...? 是礼貌请求表达。其余选项（A. Check this sentence now.；B. You must check this.；C. Why don''t you check it?）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which sentence is most polite when asking for help?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（more）。空格处应选择该项，核心理由是：knowledge 为不可数名词，但比较级结构用 more knowledge。其余选项（A. much；B. most；C. many）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'He has ______ knowledge of Chinese history than most beginners.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（brave）。空格处应选择该项，核心理由是：a brave attempt 表示“勇敢尝试”；其余选项语义不合。其余选项（A. bare；B. blank；D. brief）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The student made a ______ attempt to answer the difficult question.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（should）。空格处应选择该项，核心理由是：should have done 表示“本应该做却没做”。其余选项（A. can；B. must；C. may）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'You ______ have told me earlier; now it is too late.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（creativity）。空格处应选择该项，核心理由是：creativity 表示“创造力”，符合 solving technical problem 的语境。其余选项（A. majority；B. security；C. authority）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The young researcher showed remarkable ______ in solving the technical problem.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 C（Nevertheless）。空格处应选择该项，核心理由是：前后有让步转折关系，nevertheless 表示“尽管如此”。其余选项（A. Therefore；B. For instance；D. Likewise）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The experiment failed twice. ______, the team continued to improve the method.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（Whether）。空格处应选择该项，核心理由是：whether...or not 用来引出“是否”的两种可能，常用于宾语从句或主语从句。其余选项（A. Because；B. Unless；D. If）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '______ he comes or not, we will start the meeting at nine.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（either）。空格处应选择该项，核心理由是：两者中的任意一个用 either。其余选项（A. any；B. each；D. every）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'I have two dictionaries; you may borrow ______ of them.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（dense）。空格处应选择该项，核心理由是：dense fog 是常见搭配，表示“浓雾”。其余选项（A. heavy；C. deep；D. thickened）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The road was closed because of ______ fog.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（obtained）。空格处应选择该项，核心理由是：obtain evidence 表示“获得证据”。其余选项（A. contained；C. retained；D. maintained）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The evidence was ______ from several independent sources.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（firm）。空格处应选择该项，核心理由是：polite but firm 表示“礼貌但坚定”。其余选项（B. faint；C. false；D. flat）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The speaker''s tone was polite but ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（accused）。空格处应选择该项，核心理由是：accuse sb. of doing sth. 表示“指控某人做某事”。charge 也可表示指控，但常用 charge sb. with sth.。其余选项（B. blamed；C. charged；D. punished）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The young man was ______ of stealing the phone, but later he was proved innocent.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（due）。空格处应选择该项，核心理由是：be due to 表示“由于”；owing to 通常不用在 be 后作表语结构的核心。其余选项（A. owing；C. thanks；D. because）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The failure of the experiment was mainly ______ to poor design.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（the fewer）。空格处应选择该项，核心理由是：the more..., the fewer... 表示“越……越少”；mistakes 为可数名词复数。其余选项（A. the less；B. less；D. fewer）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The more carefully you read the question, ______ mistakes you will make.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（consistent）。空格处应选择该项，核心理由是：be consistent with 表示“与……一致”。其余选项（A. convenient；B. contrary；C. constant）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The result was ______ with what the researchers had predicted.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（relevant）。空格处应选择该项，核心理由是：be relevant to 表示“与……有关”。其余选项（A. redundant；B. resistant；C. reluctant）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new evidence is ______ to the case and should not be ignored.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（that）。空格处应选择该项，核心理由是：表语从句说明 reason 的内容时用 that，不用 because。其余选项（B. which；C. why；D. because）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The reason for his absence was ______ he had a fever.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（steadily）。空格处应选择该项，核心理由是：steadily 表示“稳定地、持续地”，与 over the past three years 搭配自然。其余选项（B. slightly；C. strictly；D. suddenly）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The number of applicants has increased ______ over the past three years.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（Participants are requested to arrive ten minutes early.）。题干所问内容应选择该项，核心理由是：正式通知应使用客观、礼貌、规范的表达。其余选项（A. You guys should come early.；B. Come early if you can.；C. Don''t be late, OK?）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which sentence is the most appropriate in a formal notice?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（that）。空格处应选择该项，核心理由是：本句是强调句型 It is/was...that...，用来强调句中某一成分。其余选项（A. which；B. when；D. where）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'It was in this library ______ she found the old manuscript.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（consensus）。空格处应选择该项，核心理由是：reach a consensus 表示“达成共识”。其余选项（A. conference；B. consequence；C. confidence）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The committee reached a ______ after three hours of discussion.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（inconvenience）。空格处应选择该项，核心理由是：inconvenience 表示“不便”；常用于道歉语境。其余选项（A. incompetence；B. independence；D. inconsistency）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The company apologized for the ______ caused by the delay.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（did they notice）。空格处应选择该项，核心理由是：Not until 置句首时，主句需部分倒装。其余选项（A. they noticed；B. they did notice；D. noticed they）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Not until the results were announced ______ the mistake.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（balanced）。空格处应选择该项，核心理由是：balanced view 表示“平衡的观点、全面的看法”。其余选项（A. brief；B. blank；D. blind）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The article presents a ______ view of the problem, considering both advantages and risks.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（attract）。空格处应选择该项，核心理由是：attract visitors 表示“吸引游客”。其余选项（B. attack；C. attend；D. attach）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The city is trying to ______ more visitors by improving public services.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（Had）。空格处应选择该项，核心理由是：虚拟条件句省略 if 时，可将 had 提前形成倒装。其余选项（B. If；C. Should；D. Were）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '______ I known the answer, I would have told you.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（conscious）。空格处应选择该项，核心理由是：a conscious effort 指“有意识的努力”。其余选项（B. conservative；C. considerable；D. constant）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The company has made a ______ effort to reduce energy consumption.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（when）。空格处应选择该项，核心理由是：固定结构：hardly/scarcely...when... 表示“一……就……”。其余选项（A. than；B. that；D. before）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Hardly had she opened the door ______ she heard someone calling her name.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（likewise）。空格处应选择该项，核心理由是：likewise 表示“同样地、也一样”。其余选项（A. likely；B. unlikely；C. otherwise）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'He completed the task quickly, and his colleagues did it ______.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（For instance）。题干所问内容应选择该项，核心理由是：For instance 表示“例如”。其余选项（A. In contrast；B. In spite of；C. As a result）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which phrase best introduces an example?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（the）。空格处应选择该项，核心理由是：形容词最高级前通常用定冠词 the。其余选项（A. 不填；B. a；C. an）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'This is ______ most useful suggestion I have received today.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（he does）。空格处应选择该项，核心理由是：比较结构中为避免重复，用助动词 does 代替 speaks English。其余选项（A. him；C. he is；D. his）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'She speaks English as fluently as ______.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 B（Certainly.）。空格处应选择该项，核心理由是：Certainly 表示礼貌许可。其余选项（A. Forget it.；C. I doubt it.；D. Not really.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— Could I use your dictionary for a moment? — ______';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（identifying）。空格处应选择该项，核心理由是：have difficulty doing sth. 表示“做某事有困难”。其余选项（A. identify；C. to identify；D. identified）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The student had difficulty ______ the main idea of the paragraph.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（to）。空格处应选择该项，核心理由是：固定搭配：appeal to sb. 表示“吸引某人；对某人有吸引力”。其余选项（A. with；B. at；C. for）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new course is designed to appeal ______ students who need practical writing skills.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（impact）。空格处应选择该项，核心理由是：have an impact on 表示“对……产生影响”。其余选项（B. import；C. image；D. impulse）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new policy will have a direct ______ on small businesses.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（conditions）。空格处应选择该项，核心理由是：working conditions 表示“工作条件”。其余选项（A. locations；B. positions；C. situations）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The workers demanded better pay and safer working ______.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（will you）。空格处应选择该项，核心理由是：否定祈使句的反意疑问部分常用 will you。其余选项（A. shall we；B. won''t you；C. do you）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Don''t forget to bring your notebook, ______?';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（Not at all.）。空格处应选择该项，核心理由是：回答 Would you mind...? 同意对方请求时常用 Not at all./Of course not.其余选项（A. It doesn''t matter.；B. Yes, please.；C. Never mind.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— Would you mind opening the window? — ______';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（has）。空格处应选择该项，核心理由是：先行词受 the only one 限定，定语从句谓语用单数 has。其余选项（A. are；B. were；D. have）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'He is the only one of the students who ______ passed the test.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 C（No, thanks.）。空格处应选择该项，核心理由是：拒绝别人提供的食物或饮品时，可用 No, thanks.其余选项（A. Good luck.；B. With pleasure.；D. Yes, please.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— Would you like some more tea? — ______ I have had enough.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（is）。空格处应选择该项，核心理由是：the number of 表示“……的数量”，作主语时谓语用单数。其余选项（B. are；C. have；D. were）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The number of students applying for the program ______ increasing.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（scheduled）。空格处应选择该项，核心理由是：be scheduled to do sth. 表示“计划、安排做某事”。其余选项（A. secured；B. selected；C. settled）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The report is ______ to be published next month.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（to solve）。空格处应选择该项，核心理由是：形容词 difficult 后常用主动形式的不定式表示被动意义。其余选项（A. to be solved；B. solving；D. solved）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The problem is difficult ______, but not impossible.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（active）。空格处应选择该项，核心理由是：take an active part in 表示“积极参与”。其余选项（B. ancient；C. accurate；D. actual）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The school encourages students to take an ______ part in class discussions.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（buying）。空格处应选择该项，核心理由是：remember doing 表示“记得做过某事”。其余选项（A. bought；C. buy；D. to buy）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'I remember ______ the book, but I cannot find it now.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（inspired）。空格处应选择该项，核心理由是：修饰人受到鼓舞用 inspired；inspiring 通常修饰事物。其余选项（A. inspected；B. installed；C. inspiring）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The students were ______ by the speaker''s personal story.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（below）。空格处应选择该项，核心理由是：表示温度、水平、标准低于某一点，常用 below zero。其余选项（A. beneath；C. underneath；D. under）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The temperature dropped ______ zero during the night.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（take）。空格处应选择该项，核心理由是：suggest 表示“建议”时，宾语从句用 should do，should 可省略。其余选项（B. took；C. has taken；D. takes）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The doctor suggested that the patient ______ more rest.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（whether）。空格处应选择该项，核心理由是：whether 引导主语从句，表示“是否”。其余选项（B. which；C. what；D. that）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'It is unclear ______ the plan will be accepted.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（What）。空格处应选择该项，核心理由是：advice 为不可数名词，感叹句用 What + 形容词 + 不可数名词。其余选项（A. How；B. What a；C. How a）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '______ useful advice he gave us!';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（repaired）。空格处应选择该项，核心理由是：have sth. done 表示“让某物被……”。其余选项（A. repairing；B. repair；D. to repair）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'She had her computer ______ yesterday.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（combination）。空格处应选择该项，核心理由是：a combination of factors 表示“多种因素的结合”。其余选项（A. collection；B. competition；C. condition）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The accident was caused by a ______ of factors, not by a single mistake.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（feasibility）。空格处应选择该项，核心理由是：feasibility 表示“可行性”，符合 practical 的语境。其余选项（A. responsibility；B. flexibility；D. visibility）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The plan sounds attractive, but its practical ______ remains uncertain.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（accordance）。空格处应选择该项，核心理由是：in accordance with 表示“按照、依据”，常与 rules、requirements、regulations 等搭配。其余选项（A. account；B. agreement；C. access）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The decision was made in ______ with school regulations.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（the）。空格处应选择该项，核心理由是：两者中较……的一个，比较级前常用 the。其余选项（A. a；C. an；D. 不填）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'He is ______ taller of the two brothers.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（cooperation）。空格处应选择该项，核心理由是：cooperation 表示“合作”，符合 team project 的语境。其余选项（B. comparison；C. composition；D. competition）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The success of the project depends largely on the team''s ______.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（is）。空格处应选择该项，核心理由是：Each of... 作主语时谓语通常用单数。其余选项（A. are；B. have；C. were）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Each of the applicants ______ required to submit a copy of the certificate.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（is）。空格处应选择该项，核心理由是：分数作主语时，谓语由 of 后名词决定；surface 是单数，故用 is。其余选项（B. have；C. has；D. are）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Three fourths of the surface of the earth ______ covered with water.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 A（Don''t lose heart.）。空格处应选择该项，核心理由是：对方受挫时，应给予鼓励。其余选项（B. You are welcome.；C. That''s wonderful.；D. It''s my pleasure.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— I failed the test again. — ______';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（that）。空格处应选择该项，核心理由是：强调句结构：It was not until...that...。其余选项（A. before；B. when；C. after）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'It was not until midnight ______ the meeting finally ended.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（ambiguous）。空格处应选择该项，核心理由是：ambiguous 表示“含糊的、有歧义的”，指表达不够明确或可能有多种理解。其余选项（A. accurate；B. adequate；C. ambitious）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The instructions were so ______ that many students misunderstood them.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（can''t）。空格处应选择该项，核心理由是：根据 her coat is still here 判断“不可能已经离开”，用 can''t have done。其余选项（A. should；B. must；D. may）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'She ______ have left already; her coat is still here.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（on）。空格处应选择该项，核心理由是：emphasis 常与介词 on 搭配，表示“对……的强调”。其余选项（A. with；B. in；D. to）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The report places special emphasis ______ environmental protection.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（intervention）。空格处应选择该项，核心理由是：medical intervention 指“医疗干预”；interference 多指“不当干涉”。其余选项（B. interruption；C. interaction；D. interference）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Treatment of the disease requires regular medical ______.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（than）。空格处应选择该项，核心理由是：固定结构：no sooner...than...，且 no sooner 置句首时主句倒装。其余选项（A. before；B. that；C. when）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'No sooner had we arrived at the station ______ the train began to move.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（on）。空格处应选择该项，核心理由是：depend on 是固定搭配，表示“取决于”。其余选项（B. to；C. of；D. with）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The final decision will depend ______ the results of the survey.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（none）。空格处应选择该项，核心理由是：三者或以上“没有一个”用 none；neither 用于两者。其余选项（A. no one；C. neither；D. nothing）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'There are many books on the shelf, but ______ of them is useful for this topic.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（support）。空格处应选择该项，核心理由是：support an answer with examples 表示“用例子支持答案”。其余选项（A. supply；B. suppose；C. survive）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The teacher asked the students to ______ their answers with examples.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 B（It doesn''t matter.）。空格处应选择该项，核心理由是：回应道歉时可用 It doesn''t matter./Never mind.其余选项（A. I hope so.；C. That''s right.；D. You are welcome.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— I''m sorry I broke your pen. — ______';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（emphasize）。空格处应选择该项，核心理由是：emphasize 表示“强调”；sympathize 表示“同情”。其余选项（B. sympathize；C. authorize；D. summarize）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The speaker tried to ______ the importance of careful preparation.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（identify）。空格处应选择该项，核心理由是：identify 是动词，表示“识别、确认”，用于说明认出或确定某事物。其余选项（A. identity；C. identification；D. identical）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The researcher tried to ______ the cause of the unexpected result.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（Although）。空格处应选择该项，核心理由是：前后存在让步关系，应用 Although。其余选项（A. Because；B. Unless；D. Since）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '______ the weather was bad, they continued the survey.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（of）。空格处应选择该项，核心理由是：固定搭配：accuse sb. of doing sth. 表示“指控某人做某事”。其余选项（A. for；B. to；D. with）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The manager was accused ______ ignoring several safety warnings before the accident.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（similar）。空格处应选择该项，核心理由是：similar 表示“相似的”，符合 not identical but... 的转折语境。其余选项（A. separate；C. specific；D. single）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The two reports are not identical, but they are ______ in many important points.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 A（as long as）。题干所问内容应选择该项，核心理由是：as long as 表示“只要”，引导条件。其余选项（B. as well as；C. as soon as；D. as far as）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which phrase best shows a condition?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（whether）。空格处应选择该项，核心理由是：ask 后接宾语从句表示“是否”时用 whether/if。其余选项（A. that；B. which；C. what）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The teacher asked us ______ we had finished the assignment.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（curiosity）。空格处应选择该项，核心理由是：curiosity about sth. 表示“对……的好奇心”。其余选项（B. security；C. certainty；D. capacity）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The child showed great ______ about how the machine worked.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（illustrate）。空格处应选择该项，核心理由是：illustrate a point 表示“说明一个观点”。其余选项（A. interrupt；B. investigate；D. imitate）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The speaker used several examples to ______ his main point.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（representative）。空格处应选择该项，核心理由是：representative sample 表示“有代表性的样本”。其余选项（A. restrictive；C. respective；D. repetitive）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The survey aims to collect data from a ______ sample of students.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（implementation）。空格处应选择该项，核心理由是：implementation 表示“实施、执行”，指把计划或政策真正落实。其余选项（A. imagination；B. implication；D. imitation）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The success of the plan depends on careful ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（invisible）。空格处应选择该项，核心理由是：invisible 表示“看不见的”；invincible 表示“不可战胜的”。其余选项（A. invaluable；C. invincible；D. invalid）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Pollution may be described as an ______ enemy because it is not always easy to see.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（confusion）。空格处应选择该项，核心理由是：avoid confusion 表示“避免混淆”。其余选项（A. conclusion；C. confidence；D. condition）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The instructions should be written in plain language to avoid ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（agreement）。空格处应选择该项，核心理由是：reach an agreement 表示“达成协议”。其余选项（B. argument；C. arrangement；D. assignment）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The two sides failed to reach an ______ on the price.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（expand）。空格处应选择该项，核心理由是：expand market share 表示“扩大市场份额”；expend 表示“花费”。其余选项（A. explore；B. extend；C. expend）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The company is looking for ways to ______ its market share.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（to）。空格处应选择该项，核心理由是：object to sth./doing sth. 表示“反对”。其余选项（A. against；C. with；D. for）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The committee objected ______ the proposal because it lacked clear evidence.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（expectations）。空格处应选择该项，核心理由是：beyond one''s expectations 表示“超出某人的预期”。其余选项（A. experiments；B. exceptions；C. expressions）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The final result was beyond our ______.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（I look forward to your reply.）。题干所问内容应选择该项，核心理由是：正式邮件结尾常用 I look forward to your reply.其余选项（A. Tell me quick!；B. See you later!；C. Write back soon!）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'This paragraph needs a more formal ending. Which expression is the most appropriate?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（have）。空格处应选择该项，核心理由是：a number of 表示“许多”，后接复数名词，谓语用复数。其余选项（A. was；B. is；C. has）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'A number of students ______ volunteered to help with the survey.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 C（Speaking.）。空格处应选择该项，核心理由是：电话中本人接听时常用 Speaking.其余选项（A. It''s me.；B. I am him.；D. I speak.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— May I speak to Mr. Brown? — ______';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（was the question）。空格处应选择该项，核心理由是：So + 形容词置句首时，主句用倒装结构。其余选项（A. the question did；B. did the question；C. the question was）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'So difficult ______ that few students could answer it correctly.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（in line）。空格处应选择该项，核心理由是：be in line with 表示“与……一致”。其余选项（B. in place；C. in turn；D. in charge）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The results are ______ with previous findings in this field.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（definite）。空格处应选择该项，核心理由是：definite 表示“明确的、确定的”，适合描述有证据支持的说法。其余选项（A. defensive；C. defective；D. delicate）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The speaker avoided making a ______ statement until more evidence was available.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（approach）。空格处应选择该项，核心理由是：approach a problem 表示“处理、看待一个问题”。其余选项（B. approve；C. appoint；D. apply）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'We need to ______ the problem from different angles.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（practical）。空格处应选择该项，核心理由是：practical 表示“实际可行的”。其余选项（A. physical；C. political；D. personal）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The plan is ______ only if enough volunteers are available.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（altitude）。空格处应选择该项，核心理由是：altitude 指“海拔高度”；attitude 是“态度”，longitude/latitude 是经纬度。其余选项（A. longitude；C. latitude；D. attitude）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The mountain village lies at an ______ of nearly 2,000 meters.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（simple）。空格处应选择该项，核心理由是：simple answer 表示“简单答案”；句意强调问题复杂。其余选项（B. similar；C. single；D. silent）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The issue is too complicated to be solved by a ______ answer.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（distinguish）。空格处应选择该项，核心理由是：distinguish between A and B 表示“区分A和B”。其余选项（A. dismiss；B. display；C. distribute）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The professor asked us to ______ between facts and opinions in the article.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（told）。空格处应选择该项，核心理由是：would rather 后接从句表示现在或将来愿望时，从句用过去式。其余选项（A. will tell；B. tell；D. have told）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'I would rather you ______ the truth now.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（convenient）。空格处应选择该项，核心理由是：convenient access 表示“便利的使用渠道”。其余选项（A. constant；C. confident；D. considerate）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The school provides students with ______ access to online learning resources.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（studying）。空格处应选择该项，核心理由是：students 与 study 为主动关系，用现在分词作后置定语。其余选项（A. to study；C. studied；D. having studied）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The students ______ in the library are preparing for the final exam.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（overview）。空格处应选择该项，核心理由是：overview 表示“概述”；overlook 是“忽视/俯瞰”。其余选项（A. outcome；C. overlook；D. overtime）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The article gives a brief ______ of the changes in modern education.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（postpone）。空格处应选择该项，核心理由是：postpone 表示“推迟”；promote 是“促进、晋升”。其余选项（A. promote；C. propose；D. prohibit）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The school decided to ______ the meeting until next Friday.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（minimize）。空格处应选择该项，核心理由是：minimize errors 表示“尽量减少错误”。其余选项（A. mention；C. maintain；D. maximum）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new system is designed to ______ errors in data entry.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（I''ll do it right away.）。空格处应选择该项，核心理由是：对礼貌请求作肯定回应，可表示马上去做。其余选项（A. You must be joking.；B. No way, thanks.；C. It doesn''t matter.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— I wonder if you could send me the file today. — ______';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（surprising）。空格处应选择该项，核心理由是：修饰事物用 surprising，表示“令人惊讶的”。其余选项（B. surprised；C. surprisingly；D. surprise）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The result was not ______; everyone had expected the team to win.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（shall we）。空格处应选择该项，核心理由是：Let''s... 的反意疑问句通常用 shall we。其余选项（A. do we；C. will you；D. do you）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Let''s discuss the question after class, ______?';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 A（Therefore）。空格处应选择该项，核心理由是：前后为因果关系，应用 therefore。其余选项（B. Nevertheless；C. Meanwhile；D. Similarly）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The data were incomplete. ______, the conclusion should be treated with caution.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（narrow）。空格处应选择该项，核心理由是：narrow 用来形容街道狭窄；thin 通常形容厚度或人瘦。其余选项（A. slight；B. thin；D. minor）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The old city is famous for its ______ streets and quiet courtyards.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（preserve）。空格处应选择该项，核心理由是：preserve 表示“保护、保存”；reserve 是“预留”。其余选项（A. observe；C. deserve；D. reserve）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The museum has taken steps to ______ rare manuscripts from damage.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（You might want to review the key points first.）。题干所问内容应选择该项，核心理由是：You might want to... 语气委婉，适合提出建议。其余选项（A. You are wrong to do that.；B. I order you to review it.；C. You have no choice.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which expression is suitable when giving advice?';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（unreliable）。空格处应选择该项，核心理由是：unreliable 表示“不可靠的”，样本量过小时，研究结果往往缺乏可靠性。其余选项（A. unavailable；C. irrelevant；D. invisible）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The results were ______ because the sample size was too small.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（far）。空格处应选择该项，核心理由是：修饰比较级可用 far/much/even 等，不能用 very。其余选项（A. very；B. too；D. so）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'This problem is ______ more difficult than the previous one.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（command）。空格处应选择该项，核心理由是：command of a language 表示“对某种语言的掌握”。其余选项（A. commerce；C. comfort；D. comment）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The course is intended to improve students'' ______ of academic English.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（convincing）。空格处应选择该项，核心理由是：convincing evidence 表示“有说服力的证据”。其余选项（B. convenient；C. conventional；D. convinced）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The report was criticized for its lack of ______ evidence.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（stimulate）。空格处应选择该项，核心理由是：stimulate growth 表示“刺激、促进增长”；simulate 是“模拟”。其余选项（A. summarize；C. simulate；D. submit）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new policy is expected to ______ economic growth.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 C（I''m sorry, but I won''t be able to attend.）。题干所问内容应选择该项，核心理由是：礼貌拒绝邀请应先表达歉意，再说明无法参加。其余选项（A. I dislike your invitation.；B. No, I don''t want to.；D. Forget it.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which response is most suitable when declining an invitation politely?';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（In conclusion）。题干所问内容应选择该项，核心理由是：In conclusion 用于引出总结性结论。其余选项（A. In case；B. In the meantime；C. In person）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which phrase best shows a conclusion in a short essay?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（will have lived）。空格处应选择该项，核心理由是：by the end of next month 指将来某时之前完成，用将来完成时。其余选项（B. have lived；C. will live；D. had lived）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'I ______ in this city for five years by the end of next month.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 A（We apologize for any inconvenience caused.）。题干所问内容应选择该项，核心理由是：正式道歉常用 We apologize for any inconvenience caused.其余选项（B. Sorry about that, whatever.；C. Bad luck for you.；D. It is not our problem.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which expression best completes a formal apology?';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（scholarship）。空格处应选择该项，核心理由是：scholarship 表示“奖学金”；其余选项不符合语境。其余选项（A. leadership；B. partnership；D. membership）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The organization offers a ______ to students from low-income families.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 B（I couldn''t agree more.）。题干所问内容应选择该项，核心理由是：I couldn''t agree more 表示“我完全同意”。其余选项（A. I can''t agree less.；C. I don''t say so.；D. I have no idea at all.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which expression best shows agreement in a discussion?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（supported）。空格处应选择该项，核心理由是：project 与 support 是被动关系，用过去分词作定语。其余选项（A. supporting；B. supports；C. to support）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The project, ______ by the local government, will start next month.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（As）。空格处应选择该项，核心理由是：As is known to all 是非限制性定语从句固定表达。其余选项（A. It；C. What；D. That）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '______ is known to all, practice is important in language learning.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（concise）。空格处应选择该项，核心理由是：concise 表示“简明的”，与 clear 并列符合语境。其余选项（B. complex；C. casual；D. confused）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'His explanation was clear and ______, so everyone understood the procedure quickly.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（when）。空格处应选择该项，核心理由是：从句中缺时间状语，先行词为 the day，故用 when。其余选项（A. which；C. what；D. that）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'I will never forget the day ______ we first met.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（valuable）。空格处应选择该项，核心理由是：valuable information 表示“有价值的信息”。其余选项（A. violent；B. various；D. valueless）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The report provides ______ information about the local economy.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 A（by contrast）。空格处应选择该项，核心理由是：前后比较对照，应用 by contrast。其余选项（B. as a result；C. in addition；D. for example）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Some students prefer online courses; ______, others learn better in a classroom.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（What）。空格处应选择该项，核心理由是：What 引导主语从句，并在从句中作宾语。其余选项（A. Which；B. That；C. It）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '______ he said at the meeting surprised everyone.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（to turn off）。空格处应选择该项，核心理由是：remember to do 表示“记得去做尚未做的事”。其余选项（A. turned off；C. turn off；D. turning off）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Please remember ______ the lights before leaving the classroom.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（is there）。空格处应选择该项，核心理由是：陈述部分含 little 表否定意义，反意疑问部分用肯定形式。其余选项（A. isn''t it；B. is it；D. isn''t there）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'There is little water left, ______?';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（consideration）。空格处应选择该项，核心理由是：under consideration 表示“正在考虑中”。其余选项（B. condition；C. connection；D. construction）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The proposal is still under ______ and no decision has been made.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（whose）。空格处应选择该项，核心理由是：whose 引导定语从句，表示所属关系。其余选项（A. what；C. which；D. that）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The book ______ cover is blue belongs to my roommate.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（discussed）。空格处应选择该项，核心理由是：question 与 discuss 之间为被动关系，用过去分词作后置定语。其余选项（A. to discuss；B. discussing；C. having discussed）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The question ______ at yesterday''s meeting remains unsolved.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（subsequently）。空格处应选择该项，核心理由是：subsequently 表示“随后、后来”，符合时间顺序。其余选项（A. previously；B. occasionally；C. frequently）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The first experiment failed; ______, the team redesigned the procedure.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（had）。空格处应选择该项，核心理由是：与现在事实相反的虚拟条件句，从句用一般过去时。其余选项（A. will have；C. had had；D. have）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'If I ______ more time, I would finish the report today.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（To obtain）。空格处应选择该项，核心理由是：句意为“为了获得更多证据”，应用不定式作目的状语。其余选项（B. Obtained；C. Having obtained；D. Obtaining）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '______ more evidence, the researchers repeated the experiment.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（why）。空格处应选择该项，核心理由是：先行词 reason 后接定语从句，表示原因时常用 why。其余选项（A. when；C. which；D. what）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The reason ______ he was late was that the bus broke down.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（account）。空格处应选择该项，核心理由是：account 可表示“叙述、描述”；give an account of sth. 是常见搭配。其余选项（A. count；C. amount；D. discount）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The witness gave a detailed ______ of what had happened at the station.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（interchangeably）。空格处应选择该项，核心理由是：interchangeably 表示“可互换地”。其余选项（B. indirectly；C. individually；D. indifferently）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The two terms are often used ______, though they are not exactly the same.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（cleaning）。空格处应选择该项，核心理由是：need doing 可表示被动含义，相当于 need to be done，主语是动作的承受者。其余选项（A. cleaned；B. clean；D. to clean）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The classroom needs ______ before the exam begins.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（to）。空格处应选择该项，核心理由是：refer to 表示“提到、参考”。其余选项（A. on；C. for；D. with）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The speaker referred ______ several recent studies in his report.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（had begun）。空格处应选择该项，核心理由是：by the time + 过去时间，主句表示此前已完成的动作，用过去完成时。其余选项（A. begins；B. began；D. has begun）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'By the time we arrived, the lecture ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（distinction）。空格处应选择该项，核心理由是：make a distinction between A and B 表示“区分A和B”。其余选项（A. decision；B. distribution；C. description）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'He made a clear ______ between short-term goals and long-term goals.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（as a result）。空格处应选择该项，核心理由是：前后为结果关系，as a result 表示“因此”。其余选项（A. on the contrary；B. for example；C. in contrast）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The professor speaks slowly and clearly; ______, his lectures are easy to follow.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（hearing）。空格处应选择该项，核心理由是：look forward to 中 to 为介词，后接动名词。其余选项（A. to hear；C. heard；D. hear）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'She is looking forward to ______ from the university.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 A（Moreover）。空格处应选择该项，核心理由是：前后为递进关系，应用 moreover。其余选项（B. Otherwise；C. However；D. Instead）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The first method is expensive. ______, it takes too much time.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（awareness）。空格处应选择该项，核心理由是：raise awareness of sth. 表示“提高对……的意识”。其余选项（A. arrangement；C. agreement；D. assistance）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The program aims to raise students'' ______ of environmental protection.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（is）。空格处应选择该项，核心理由是：主语中心词是 The book，together with 不影响谓语单复数，故用 is。其余选项（A. are；B. have been；C. were）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The book, together with the notes, ______ on the desk.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（in despair）。空格处应选择该项，核心理由是：in despair 表示“绝望地”，符合语境。其余选项（A. in dispute；C. in dismay；D. in default）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'You should not sit down ______ and do nothing when difficulties appear.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（because）。空格处应选择该项，核心理由是：空后是完整从句，应用 because；because of/due to/owing to 后接名词短语。其余选项（A. because of；B. due to；D. owing to）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The meeting was put off ______ the chairman was ill.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（converted）。空格处应选择该项，核心理由是：convert A into B 表示“把A转变为B”。其余选项（A. confined；C. connected；D. convinced）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The old factory has been ______ into a modern art center.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（improve）。空格处应选择该项，核心理由是：improve public transport 表示“改善公共交通”。其余选项（B. remove；C. prove；D. approve）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The mayor promised to ______ public transport in the next five years.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（except）。空格处应选择该项，核心理由是：except Monday 表示“除周一外”；besides 表示“除……之外还”。其余选项（A. except for；B. besides；D. beside）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The museum is open every day ______ Monday.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（promote）。空格处应选择该项，核心理由是：promote 表示“促进、推动”，强调支持某事物的发展。其余选项（A. propose；B. produce；C. prohibit）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The policy is intended to ______ equal opportunities for all students.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（additional）。空格处应选择该项，核心理由是：additional documents 表示“补充文件、额外文件”。其余选项（A. adjective；B. addictive；D. adequate）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The applicant was asked to provide ______ documents before the deadline.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（when）。空格处应选择该项，核心理由是：idea 后接同位语从句，句意为“不知道他何时回来”。其余选项（B. which；C. what；D. that）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'I have no idea ______ he will come back.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（to read）。空格处应选择该项，核心理由是：make sb. do sth. 变被动语态时，不定式符号 to 要还原。其余选项（A. to reading；B. reading；C. read）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The students were made ______ the sentence again.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（straightforward）。空格处应选择该项，核心理由是：straightforward 表示“简单明了的”。其余选项（A. far-reaching；B. hard-working；C. forward-looking）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The instructions are ______ enough for beginners to follow.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（reduce）。空格处应选择该项，核心理由是：reduce pollution 表示“减少污染”。其余选项（A. replace；C. recover；D. release）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The government has introduced measures to ______ air pollution.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 A（The results suggest that further research is needed.）。题干所问内容应选择该项，核心理由是：学术表达应客观、准确，suggest that further research is needed 更自然正式。其余选项（B. The results say we need more stuff.；C. The results tell everyone to do things.；D. The results are like very useful.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Which sentence sounds most natural in academic writing?';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（will）。空格处应选择该项，核心理由是：the more..., the more... 结构中可用一般现在/将来表达规律或结果。其余选项（B. should；C. would；D. must）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The more practice you get, the more confident you ______ become.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（did he realize）。空格处应选择该项，核心理由是：Only + 状语置于句首时，主句需部分倒装。其余选项（B. he realized；C. realized he；D. he did realize）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Only after the exam ______ how important daily review was.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（took）。空格处应选择该项，核心理由是：It is high time that... 从句常用过去式表示“早该做某事”。其余选项（A. have taken；C. will take；D. take）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'It is high time that we ______ action to solve the problem.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（because of）。空格处应选择该项，核心理由是：because of 后接名词短语；because/since/as 后接从句。其余选项（A. as；B. since；D. because）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The student was absent from class ______ illness.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（detailed）。空格处应选择该项，核心理由是：detailed explanation 表示“详细解释”。其余选项（A. determined；B. detained；C. detached）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The committee asked for a more ______ explanation of the budget.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（reluctant）。空格处应选择该项，核心理由是：be reluctant to do sth. 表示“不情愿做某事”。其余选项（A. relevant；B. resistant；D. redundant）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The villagers were ______ to leave their homes after the flood warning.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（no）。空格处应选择该项，核心理由是：make no decision 表示“没有作出决定”；not 不能直接修饰名词 decision。其余选项（A. neither；B. none；C. not）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The committee has made ______ decision yet.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 B（However）。空格处应选择该项，核心理由是：前后转折，应用 however。其余选项（A. Therefore；C. Likewise；D. Besides）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The plan sounds attractive. ______, it may be difficult to carry out.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（will be completed）。空格处应选择该项，核心理由是：bridge 与 complete 是被动关系，且指将来动作，用 will be done。其余选项（A. completed；B. will complete；D. has completed）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The bridge ______ before the rainy season begins.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（taking）。空格处应选择该项，核心理由是：deny 后接动名词作宾语。其余选项（A. to take；C. take；D. took）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The man denied ______ the document without permission.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（can''t）。空格处应选择该项，核心理由是：根据门锁着推测“不可能在家”，用 can''t 表示否定推测。其余选项（A. need；B. shall；D. must）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The door is locked. He ______ be at home.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（redundant）。空格处应选择该项，核心理由是：redundant 表示“多余的、冗余的”；abundant 是“丰富的”。其余选项（A. abundant；B. reluctant；D. relevant）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Some documents were found to be ______ because they repeated information already provided.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（of）。空格处应选择该项，核心理由是：ahead of schedule 表示“提前”。其余选项（B. for；C. to；D. with）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The project was completed ahead ______ schedule.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（where）。空格处应选择该项，核心理由是：从句中缺地点状语，先行词为 school，故用 where。其余选项（A. that；B. what；D. which）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'This is the school ______ I studied five years ago.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（have）。空格处应选择该项，核心理由是：定语从句先行词为 students，谓语用复数 have。其余选项（A. has；B. was；D. is）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'He is one of the students who ______ passed the test.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（so that）。空格处应选择该项，核心理由是：so that 引导目的状语从句，表示“以便”。其余选项（A. even if；C. as though；D. now that）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The data were collected carefully ______ errors could be reduced.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（observation）。空格处应选择该项，核心理由是：observation 表示“观察”，与 rather than guesswork 构成对比。其余选项（A. opposition；C. operation；D. occupation）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The scientist''s argument was based on careful ______ rather than guesswork.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 B（Good idea.）。空格处应选择该项，核心理由是：对建议表示赞同可用 Good idea.其余选项（A. No wonder.；C. That''s all right.；D. Never mind.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— Shall we go over the grammar exercises now? — ______';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（informative）。空格处应选择该项，核心理由是：informative 表示“信息量大的、有启发的”。其余选项（B. informal；C. imaginary；D. inactive）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The professor''s remarks were brief but highly ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（to）。空格处应选择该项，核心理由是：apply to sb./sth. 表示“适用于”。其余选项（B. with；C. at；D. for）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new rule applies ______ all students, including exchange students.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（of）。空格处应选择该项，核心理由是：be capable of doing sth. 是固定结构，表示“有能力做某事”。其余选项（A. for；C. to；D. with）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The student is capable ______ solving the problem independently.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（uninhabited）。空格处应选择该项，核心理由是：uninhabited 表示“无人居住的”；habitable 表示“适合居住的”。其余选项（B. inhabitant；C. habitable；D. inhabited）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The remote island is largely ______, with only a few researchers visiting it each year.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（truthful）。空格处应选择该项，核心理由是：truthful account 表示“真实陈述”；trustful 指“轻信的”。其余选项（A. true；B. trustful；C. trusted）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The judge asked the witness to give a ______ account of the event.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（ascertain）。空格处应选择该项，核心理由是：ascertain 表示“查明、确定”；assume 是“假设”，assert 是“断言”，assign 是“分配”。其余选项（A. assign；C. assume；D. assert）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The research team tried to ______ whether the new policy was effective.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（that）。空格处应选择该项，核心理由是：recommendation 后接同位语从句，说明建议内容，用 that 引导。其余选项（A. it；C. what；D. which）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'It is the recommendation ______ students review their notes every week.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（express）。空格处应选择该项，核心理由是：express one''s views 表示“表达观点”。其余选项（B. extend；C. expand；D. expose）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The professor encouraged students to ______ their own views in the discussion.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 B（would have found）。空格处应选择该项，核心理由是：与过去事实相反的虚拟条件句，主句用 would have done。其余选项（A. found；C. will have found；D. would find）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'If he had checked the data carefully, he ______ the mistake.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（obey）。题干所问内容应选择该项，核心理由是：observe 在此表示“遵守”，与 rules/laws 搭配时相当于 obey。其余选项（A. predict；C. notice；D. watch）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'Students are expected to observe the rules even when no teacher is present.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（restored）。空格处应选择该项，核心理由是：restore 表示“修复、恢复”，指把事物恢复到原来的状态。其余选项（A. reserved；B. renewed；C. refreshed）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The old building was ______ after years of careful repair.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 C（Instead）。空格处应选择该项，核心理由是：instead 表示“作为替代”。其余选项（A. Therefore；B. Besides；D. Likewise）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'I cannot attend the meeting. ______, I will send my notes to the group.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（provided that）。空格处应选择该项，核心理由是：provided that 表示“只要、如果”，引导条件状语从句。其余选项（B. so that；C. even though；D. as if）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'You can borrow the book ______ you return it by Friday.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 D（to be）。空格处应选择该项，核心理由是：pretend to do sth. 表示“假装做某事”。其余选项（A. being；B. been；C. be）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The boy pretended ______ asleep when his mother entered the room.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（contradict）。空格处应选择该项，核心理由是：contradict 表示“与……矛盾”。其余选项（A. conduct；B. contribute；D. construct）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new evidence seems to ______ his earlier statement.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（caution）。空格处应选择该项，核心理由是：with caution 表示“谨慎地”。其余选项（B. courage；C. custom；D. comfort）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The medicine may have side effects, so it should be used with ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（critical）。空格处应选择该项，核心理由是：critical thinking 表示“批判性思维”。其余选项（B. critic；C. crucial；D. creative）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The course aims to help students develop ______ thinking.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（with）。空格处应选择该项，核心理由是：be familiar with sth. 表示“熟悉某事”。其余选项（A. to；B. about；D. for）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The researcher is familiar ______ both qualitative and quantitative methods.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 B（Congratulations!）。空格处应选择该项，核心理由是：听到好消息时应表示祝贺。其余选项（A. Take care!；C. What a pity!；D. Never mind!）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— I have passed the entrance examination. — ______';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 A（clause）。空格处应选择该项，核心理由是：clause 表示“从句、分句”；复合句含有多个分句。其余选项（B. letter；C. word；D. phrase）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The sentence is difficult because it contains more than one ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（accessible）。空格处应选择该项，核心理由是：be accessible to 表示“可进入、可使用”。其余选项（A. acceptable；B. adaptable；D. available）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The public library is ______ to everyone in the community.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（direct）。空格处应选择该项，核心理由是：direct railway line 表示“直达铁路线路”。其余选项（A. direction；B. directive；D. director）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The two cities are connected by a ______ railway line.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（is being revised）。空格处应选择该项，核心理由是：now 表示正在进行，report 与 revise 是被动关系，故用现在进行时被动语态。其余选项（A. is revised；B. has revised；D. revises）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The report ______ now, so we cannot read it yet.';

update public.questions
set explanation = '本题考查语法结构，需要先判断句子成分、时态语态或从句关系，再选择符合规则的形式。正确答案为 C（read）。空格处应选择该项，核心理由是：make sb. do sth. 主动语态中不定式省略 to。其余选项（A. reading；B. to read；D. readed）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要优先检查谓语形式、非谓语形式、从句连接词和固定句型是否与题干结构一致。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The teacher made the students ______ the sentence again.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（concern）。空格处应选择该项，核心理由是：issues of common concern 表示“共同关心的问题”。其余选项（A. command；C. content；D. control）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The meeting was held to discuss issues of common ______.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（justify）。空格处应选择该项，核心理由是：justify 表示“证明……有理、为……提供正当理由”。其余选项（A. modify；B. identify；D. classify）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The evidence is not strong enough to ______ the conclusion.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 C（benefit）。空格处应选择该项，核心理由是：be of great benefit to sb. 表示“对某人大有益处”。其余选项（A. profit；B. interest；D. advantage）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The teacher''s advice was of great ______ to the new students.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（on）。空格处应选择该项，核心理由是：cast doubt on 表示“使……受到怀疑”，即让某事显得不确定或不可信。其余选项（B. to；C. for；D. with）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The new evidence cast doubt ______ the original conclusion.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 B（steady）。空格处应选择该项，核心理由是：steady improvement 表示“稳定进步”。其余选项（A. strict；C. stiff；D. steep）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The student was praised for his ______ improvement in writing.';

update public.questions
set explanation = '本题考查语用功能和语篇衔接，需要根据交际场景或上下文关系选择最得体的表达。正确答案为 D（My pleasure.）。空格处应选择该项，核心理由是：回应感谢可用 My pleasure./You''re welcome.其余选项（A. No, thanks.；B. I agree.；C. Never mind.）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。排除选项时，要注意表达的礼貌程度、逻辑关系和语篇功能，不能只凭字面意思选择。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = '— Thank you for helping me with the report. — ______';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（relevant）。空格处应选择该项，核心理由是：be relevant to 表示“与……相关”。其余选项（B. regular；C. reliable；D. relative）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The applicant''s experience is highly ______ to the position.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 A（consistent）。空格处应选择该项，核心理由是：be consistent with 表示“与……一致”。其余选项（B. constant；C. considerate；D. conscious）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The plan was rejected because it was not ______ with the current regulations.';

update public.questions
set explanation = '本题考查词汇辨析或固定搭配，需要结合空格前后的语境判断最自然、最准确的表达。正确答案为 D（to）。空格处应选择该项，核心理由是：pay attention to 是固定搭配。其余选项（A. on；B. with；C. for）虽然可能在形式上相近，但不能同时满足本句的语义、语法或固定搭配要求。做这类题时，不要只看单个词的中文意思，还要看它能否与题干中的名词、介词或动词形成固定搭配。'
where exam_code = 'COMMON'
  and subject = '英语运用'
  and module = '语言知识'
  and stem = 'The teacher reminded us to pay attention ______ spelling and punctuation.';

commit;
