export type ResponseMetrics = {
  response_time_sec: number;
  tokens_generated: number;
  prompt_tokens: number;
  tokens_per_sec: number;
  model: string;
};

export type Message = {
  text: string;
  sender: "user" | "assistant";
  metrics?: ResponseMetrics;
};
