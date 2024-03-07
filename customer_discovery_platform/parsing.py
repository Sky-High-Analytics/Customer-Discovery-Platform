import re
from typing import List, Dict
from langchain.output_parsers import RegexParser


# To handle answers that have an odd format, we need some extra regex
# I found this solution at https://github.com/langchain-ai/langchain/issues/1358
class RefinedRegexParser(RegexParser):
    """This is just RegexParser. But instead of throwing a parse error, 
    it just returns 0."""

    regex=r"Score: ([0-9]+)\n(.*?)"
    output_keys:List[str] =["answer", "score"]
        
    def parse(self, text: str) -> Dict[str, str]:
        """Parse the output of an LLM call."""
        match = re.search(self.regex, text)
        if match:
            return {key: match.group(i + 1) for i, key in enumerate(self.output_keys)}
        else:
            # If text in unparsable, just return a score of 0
            return {
                "answer": text,
                "score": 0,
            }