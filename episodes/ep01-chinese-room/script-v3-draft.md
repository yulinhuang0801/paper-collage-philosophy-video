# Episode 1 script v3 (draft, not recorded)

A spoken-style rewrite of the v2.1 narration (`references/episode-1-script-v2-full.md`). The text the TTS reads is in `segments-v3-draft.json`. `segments.json` stays the published cut, because the timing tests check against it.

Status: waiting for gate 1 (script read for fluency). Nothing has been re-recorded.

## What changed

**English** (the main problem was that it read like an essay):  
- Contractions everywhere (don't, it's, you'd). The old "You do not speak Chinese. You cannot read Chinese." sounded robotic when read aloud.  
- Shorter sentences, and the way a person talks: "Not a word.", "Now flip it around.", "Searle's answer was, wait a second."  
- Concrete details instead of abstract wording: "turn to page two hundred and twelve", "comfort you on a bad day", "a lunch from when you were a kid".  
- Less "That is the…", "It is…" and "Here is where…" padding.  
- Fixed two lines the subtitle splitter cut into fragments: the quoted word list ("food," "happy," "noodles") and "apple" in the middle of a sentence, which became 4 and 2 subtitle pieces.

**Chinese** (already conversational; I cut the translated-from-English feel):  
- "背后那个让人不太舒服的想法" → "这个让人有点不舒服的想法，来自……中文房间", ending on the name.  
- "以对的方式连在一起" / "组织起来的系统" → "按对的方式连起来" / "整个系统".  
- More spoken words: 中文很溜, 好得没话说, 那道坎, 接住你很私人的心事, 滴水不漏.  
- The rule book gets a concrete page: 翻到第二百一十二页.

**Kept word for word:** the unified question in both languages, and the phrases the 8D2 overlays anchor to (Being able to produce the right words / Knowing what those words mean; 能说出对的词 / 知道这些词是什么意思).

**Length:** English goes from 5,639 to about 5,520 characters, Chinese from 1,766 to 1,759, so the runtime stays about the same.

## Wiring into the pipeline (after gate 1 and re-recording)

Chinese sentence counts per segment are unchanged, so no Chinese shot ranges change. English shot ranges that change in `episode.json`:

| Shot | old en | new en |
|---|---|---|
| 1A / 1B / 1C | [0,1] / [2,4] / [5,-1] | [0,0] / [1,3] / [4,-1] |
| 4C / 4D / 4E | [4,6] / [7,8] / [9,-1] | [4,5] / [6,7] / [8,-1] |
| 5C / 5D1 / 5D2 / 5E | [4,5] / [6,11] / [12,15] / [16,-1] | [4,6] / [7,12] / [13,15] / [16,-1] |
| 9A / 9B / 9C | [0] / [1,2] / [3,-1] | [0,1] / [2,3] / [4,-1] |

The 7A-1 / 7A-2 cut phrase becomes `你一个人就是整个系统` / `and became the entire system`.

Checked with `pipeline timing` on a copy of the episode, using the old recorded lengths: every sentence lands in a shot, and both languages pass the guardrails. Re-run `measure` and `timing` on the real recording.

## 1. Hook (K1)

**EN**

What if something could answer every question you ask, perfectly, without understanding a single word?  
It could explain love.  
It could write you a poem.  
It could comfort you on a bad day.  
And all the while, there might be no one inside who knows what any of it means.  
That's the unsettling idea behind one of the most famous thought experiments in philosophy.  
It's called the Chinese Room.

**ZH**

有没有可能，一个东西能把你问的每个问题都答得完美，却一个字都不懂？  
它能跟你聊什么是爱，能给你写诗，能在你难过的时候安慰你。  
可在它里面，也许根本没有谁知道，这些话到底是什么意思。  
这个让人有点不舒服的想法，来自哲学里最有名的思想实验之一：中文房间。

## 2. Enter the room (K2)

**EN**

Picture yourself locked in a room.  
Every so often, someone outside slides a sheet of paper through a little slot in the wall.  
It's covered in Chinese characters.  
And you don't know any Chinese.  
Not a word.  
To you, those characters are just shapes, little strokes and boxes and squiggles.  
But there's one more thing in the room, a huge book of instructions.  
And it's absurdly detailed.  
It says things like, when you see these symbols, turn to page two hundred and twelve.  
Copy down the symbols you find there.  
Then push the paper back out through the slot.  
So that's what you do.  
A note comes in.  
You look it up.  
A note goes out.  
Then another one comes in, and you do it all again.

**ZH**

想象一下，你被关在一个房间里。  
时不时地，外面有人从墙上的小口塞进来一张纸，上面写满了中文。  
可你不懂中文，一个字都不认识。  
在你眼里，这些字就是一堆形状：点点横横，小方框，弯弯绕绕的线。  
不过房间里还有一样东西：一本厚得吓人的说明书。  
它写得细到离谱。  
比如：看到这几个符号，就翻到第二百一十二页，把那一页上的符号抄到新纸上，再从小口塞出去。  
那你就照做。  
一张纸进来，你翻书，抄好，塞出去。  
又一张进来，你再来一遍。

## 3. The conversation (K3)

**EN**

After a while, you get so good at this that the people outside are sure they're chatting with a fluent Chinese speaker.  
They ask you, "What's your favorite food?"  
And you slide back the symbols that mean "I love noodles."  
They ask, "Are you happy today?"  
And you send back something warm and natural.  
From the outside, it looks like you understand Chinese perfectly.  
But inside, you still have no idea what food or happy or noodles actually mean.  
You're just following the rules.

**ZH**

慢慢地，你回得越来越像样。  
外面的人都确信，自己是在跟一个中文很溜的人聊天。  
他们问：你最喜欢吃什么？  
你塞回去一串符号，意思是：我最爱吃面条。  
他们问：你今天开心吗？  
你回了一句很暖、很自然的话。  
从外面看，你的中文好得没话说。  
可在房间里，你还是不知道“吃”“开心”“面条”是什么意思。  
你只是在照着规则办事。

## 4. The question behind it (K4)

**EN**

This thought experiment comes from the philosopher John Searle, back in 1980.  
He was going after an idea that sounds pretty reasonable: if a computer acts like it understands language, then maybe it really does.  
Searle's answer was, wait a second.  
A computer can take in symbols, follow rules, and give back convincing answers.  
But is that the same as knowing what the symbols mean?  
It's the gap between seeming to understand, and actually understanding.  
And these days, that's not science fiction anymore.  
When an AI explains something hard, writes a message that sounds just like you, or answers something really personal, it can feel strangely human.  
But this is exactly where the Chinese Room tells us to slow down.  
Sounding fluent doesn't automatically mean understanding.

**ZH**

这个思想实验，是哲学家约翰·塞尔在 1980 年提出来的。  
他想反驳的，是一个听上去挺有道理的说法：一台机器如果表现得像是懂语言，那它是不是就真的懂？  
塞尔说：等一下。  
计算机确实能接收符号，执行规则，给出像模像样的回答。  
可这跟知道这些符号是什么意思，是一回事吗？  
这就是“看起来懂”和“真的懂”之间的那道坎。  
而放到今天，这事已经一点都不科幻了。  
AI 能把很难的概念讲明白，能学着你的语气写消息，能接住你很私人的心事，有时候真会让你觉得，屏幕对面坐着一个人。  
但中文房间想让我们先停一停：说得流利，就等于理解了吗？

## 5. Think with it (K5)

**EN**

So here's where it gets personal.  
What do you think understanding actually is?  
A calculator can solve a really hard equation.  
But hardly anyone would say it understands math the way a mathematician does.  
Now flip it around.  
A dog can't tell you what loyalty means.  
But when it knows you at the door, waits for you to come home, or notices when you're sad, it feels wrong to say it understands nothing.  
So maybe language isn't the whole story.  
Think about the word "apple."  
When you hear it, maybe you see a color.  
Maybe you hear the crunch when you bite into one.  
The sweetness, the smell, some lunch from when you were a kid.  
That word is tied to a world you've actually lived in.  
So if a machine uses the word apple perfectly, does it have anything like that?  
Does it even need to?  
Or is understanding just knowing how to use a word the right way, every time?  
Take a few seconds before you answer.  
Because your answer depends on what you think a mind is.

**ZH**

说到这儿，这个问题就跟你有关了。  
你觉得，理解到底是什么？  
计算器能解出很难的方程。  
但很少有人会说，计算器像数学家那样懂数学。  
反过来，狗没法跟你解释什么叫忠诚。  
可它会在门口认出你，会等你回家，会在你难过的时候凑过来。  
你很难说它什么都不懂。  
所以，语言可能不是全部。  
想一想“苹果”这个词。  
听到它，你可能会想到一种颜色，想到咬下去那一声脆响，想到那股甜味和香味，或者小时候的某一顿午饭。  
这个词，连着你真真切切活过的那个世界。  
可如果一个系统能把“苹果”这个词用得滴水不漏，它里面有这种连接吗？  
它需要有吗？  
还是说，所谓理解，就是在任何场合都能把一个词用对？  
先别急着选。  
停几秒，想一想。  
你的答案，取决于你觉得心灵到底是什么。

## 6. The strongest objection (K6)

**EN**

Now, there's an obvious comeback to Searle's room.  
Sure, the person inside doesn't understand Chinese.  
But what if the whole room does?  
The person is just one piece of a bigger system.  
There's also the book, all the rules, the notes coming in and going out, and the way it all works together.  
Maybe together, the system understands Chinese, even if no single part of it does.  
Think about your own brain.  
One neuron doesn't get a joke.  
One neuron doesn't know your name.  
It's just one tiny cell, sending signals.  
But wire up tens of billions of them in the right way, and somehow you get memories, thoughts, a sense of humor, and an understanding of language.  
So the systems reply asks, why should any one part of a computer have to understand?  
Maybe understanding belongs to the whole system.

**ZH**

不过，对塞尔这个房间，有一个很自然的反驳。  
好，房间里的人确实不懂中文。  
但会不会，整个房间是懂的？  
人只是这个系统里的一个零件。  
系统里还有那本说明书，那些规则，进进出出的纸条，还有它们彼此配合的方式。  
合在一起，也许它就懂中文了，哪怕其中任何一个零件都不懂。  
想想你自己的大脑。  
一个神经元，听不懂笑话。  
一个神经元，也不知道你叫什么。  
它就是一个小小的细胞，在发信号而已。  
可是几百亿个神经元按对的方式连起来，就有了你的记忆、你的念头、你的幽默感，还有你对语言的理解。  
所以这个反驳问的是：凭什么要求计算机里的某一个零件懂？  
理解，也许属于整个系统。

## 7. Searle's answer and the standoff (K7)

**EN**

Searle's answer was this: even if you memorized the whole book, did every step in your head, and became the entire system yourself, you still wouldn't understand Chinese.  
You'd just be shuffling symbols around, without knowing what any of them mean.  
So that's the standoff.  
One side says that if you organize enough symbol processing, understanding can grow out of it.  
The other side says symbols on their own will never be enough.

**ZH**

塞尔的回答是：就算你把整本书背下来，所有步骤都在脑子里走一遍，你一个人就是整个系统，你还是不懂中文。  
你还是只是在搬弄符号，并不知道它们是什么意思。  
僵局就在这儿。  
一方说，符号处理只要组织得足够复杂，理解就会从里面长出来。  
另一方说，光靠符号，永远不够。

## 8. Why there may be no quick answer (K8)

**EN**

Maybe what's missing is a connection to the world.  
Maybe words only mean something when they're tied to seeing, touching, doing, remembering, caring, being moved by things.  
Or maybe that's just human bias.  
Maybe we assume a mind has to work like ours, because ours is the only one we've ever seen from the inside.  
The Chinese Room doesn't prove that machines can never understand.  
And it doesn't prove that today's AI understands, either.  
What it does is make one difference really hard to ignore.  
Being able to produce the right words is one thing.  
Knowing what those words mean might be something else.

**ZH**

缺的那一块，也许是和世界的连接。  
也许词语只有跟别的东西绑在一起，才真正有意义：看见，摸到，动手，记住，在乎，或者被什么事触动。  
当然，这也可能只是人类的偏见。  
也许我们默认，智能就得长成我们这样，只因为这是我们唯一从里面认识过的智能。  
中文房间证明不了，机器永远不可能懂。  
它也证明不了，今天的 AI 已经懂了。  
它只是把一个区别摆在你面前，让你很难绕过去：能说出对的词，是一回事。  
知道这些词是什么意思，可能是另一回事。

## 9. Ending (K9)

**EN**

So here's my question for you.  
When AI gives a perfect answer, is it understanding, or only following rules?  
If you think it understands, what's your strongest reason?  
And if you think it's only following rules, what would it take to change your mind?  
Maybe something can sound completely intelligent and understand nothing at all.  
Or maybe understanding is just what happens when the pattern gets complex enough.

**ZH**

所以，最后这个问题留给你：当 AI 给出一个完美的回答，它是理解了，还是只是在遵守规则？  
如果你觉得它懂了，你最有力的理由是什么？  
如果你觉得它只是在遵守规则，那它还得具备什么，你才会改变想法？  
也许，一个东西可以听上去聪明极了，却什么都不懂。  
也许，当模式复杂到一定程度，理解就是这样发生的。  
