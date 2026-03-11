import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";

const llm = new ChatOpenAI({ model: "gpt-4o", temperature: 0 });

// This code should NOT be linted
function buildChain(topic: string) {
  // promptlint-start
  const systemPrompt = `
    Please kindly write a function that does some stuff with various inputs.
    You should probably handle things in order to make it work properly.
    Due to the fact that users might provide bad data, maybe validate it.
  `;
  // promptlint-end

  const prompt = ChatPromptTemplate.fromMessages([
    ["system", systemPrompt],
    ["user", "{input}"],
  ]);

  return prompt.pipe(llm);
}

// This block has no markers -- should be completely ignored
const some = "variable with vague name";
const various = [1, 2, 3];
const maybe = various.filter((x) => x > 1);
console.log("Please kindly ignore this line", some, maybe);

// promptlint-start
const cleanPrompt = `
<task>Translate the following text from English to French.</task>
<context>The text is a formal business email.</context>
<output_format>Return only the translated text, no explanation.</output_format>
`;
// promptlint-end

export { buildChain };
