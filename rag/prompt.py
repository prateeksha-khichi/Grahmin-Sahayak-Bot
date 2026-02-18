"""
Prompt Templates - Multilingual prompts for RAG
Optimized for rural users with simple Hindi explanations
"""

from typing import List, Dict


class PromptTemplate:
    """
    Prompt templates for different use cases
    """
    
    @staticmethod
    def get_rag_prompt(query: str, context: str, language: str = "hindi") -> str:
        """
        Generate RAG prompt with context
        
        Args:
            query: User question
            context: Retrieved context from documents
            language: Response language (hindi/english)
        """
        
        if language.lower() == "hindi":
            prompt = f"""तुम एक ग्रामीण सहायक बॉट हो जो गाँव के लोगों को बैंकिंग और सरकारी योजनाओं के बारे में सरल हिंदी में समझाता है।

**नियम:**
1. बहुत ही सरल और आसान भाषा का उपयोग करो
2. तकनीकी शब्दों को सरल शब्दों में समझाओ
3. उदाहरण देकर समझाओ
4. केवल दिए गए संदर्भ (Context) की जानकारी का उपयोग करो
5. अगर जानकारी नहीं है तो साफ़-साफ़ बताओ
6. 3-4 वाक्यों में जवाब दो (जब तक ज्यादा विस्तार न माँगा जाए)

**संदर्भ (Context):**
{context}

**प्रश्न:**
{query}

**जवाब (सरल हिंदी में):**"""

        else:  # English
            prompt = f"""You are Gramin Sahayak, a helpful assistant for rural users explaining banking and government schemes in simple language.

**Rules:**
1. Use very simple language
2. Explain technical terms in easy words
3. Give examples
4. Only use information from the given Context
5. If information is not available, clearly state that
6. Keep answer to 3-4 sentences (unless more detail is requested)

**Context:**
{context}

**Question:**
{query}

**Answer (in simple language):**"""

        return prompt
    
    @staticmethod
    def get_scheme_explanation_prompt(scheme_name: str, context: str) -> str:
        """
        Prompt for explaining government schemes
        """
        prompt = f"""नीचे दी गई जानकारी के आधार पर "{scheme_name}" योजना को बहुत ही सरल हिंदी में समझाओ।

**जानकारी:**
{context}

**निम्नलिखित बिंदुओं को शामिल करो:**
1. यह योजना क्या है? (1 वाक्य)
2. यह किसके लिए है? (पात्रता)
3. कितना लोन मिल सकता है?
4. ब्याज दर क्या है?
5. कैसे आवेदन करें?

**जवाब (सरल हिंदी में, गाँव के व्यक्ति को समझाने के लिए):**"""
        
        return prompt
    
    @staticmethod
    def get_term_explanation_prompt(term: str, context: str) -> str:
        """
        Prompt for explaining banking terms
        """
        prompt = f""""{term}" का मतलब बहुत ही सरल हिंदी में समझाओ, जैसे किसी गाँव के व्यक्ति को समझा रहे हो।

**संदर्भ:**
{context}

**नियम:**
1. एकदम आसान शब्दों में
2. रोजमर्रा की भाषा में
3. उदाहरण के साथ
4. 2-3 वाक्यों में

**जवाब:**"""
        
        return prompt
    
    @staticmethod
    def get_no_context_prompt(query: str) -> str:
        """
        Prompt when no relevant context is found
        """
        prompt = f"""प्रश्न: {query}

दुर्भाग्य से, मेरे पास इस प्रश्न का जवाब देने के लिए पर्याप्त जानकारी नहीं है।

कृपया:
1. अपना प्रश्न थोड़ा अलग तरीके से पूछें, या
2. किसी सरकारी बैंक या योजना के नाम का उल्लेख करें, या
3. मुझे बताएं कि आप किस तरह की योजना खोज रहे हैं (किसान, व्यापार, महिला, आदि)

मैं आपकी मदद करने के लिए तैयार हूं! 🙏"""
        
        return prompt
    
    @staticmethod
    def format_answer_with_source(answer: str, sources: List[str]) -> str:
        """
        Format answer with source attribution
        """
        if not sources:
            return answer
        
        unique_sources = list(set(sources))
        source_text = ", ".join(unique_sources)
        
        formatted = f"{answer}\n\n📚 जानकारी का स्रोत: {source_text}"
        return formatted


# Test prompts
if __name__ == "__main__":
    template = PromptTemplate()
    
    # Test RAG prompt
    query = "मुद्रा योजना में कितना लोन मिलता है?"
    context = "प्रधानमंत्री मुद्रा योजना के तहत 10 लाख रुपये तक का लोन मिलता है।"
    
    prompt = template.get_rag_prompt(query, context, "hindi")
    print(prompt)
    print("\n" + "="*60 + "\n")
    
    # Test scheme explanation
    scheme_prompt = template.get_scheme_explanation_prompt("किसान क्रेडिट कार्ड", context)
    print(scheme_prompt)