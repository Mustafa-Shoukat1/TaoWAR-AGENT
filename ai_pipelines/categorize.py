from openai import OpenAI
import os
import json
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

# Define Pydantic model for structured output
class CategoryResponse(BaseModel):
    categories: List[str] = Field(description="List of category names that the post belongs to")

# Initialize OpenAI client
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_prompt(post, categories_dict):
    # Create parser for our Pydantic model
    parser = PydanticOutputParser(pydantic_object=CategoryResponse)
    
    # Create prompt template with proper formatting instructions
    template = """
    Post:
    "{text}"
    
    Categories: Remember that give Complete names of categories
    {categories}
    
    Based on the post content, determine which categories the post belongs to.
    Only include categories where there's a match based on the category description.
    The post can belong to more than one category but if it does not belong to any then you should return empty list []
    
    {format_instructions}
    """
    
    # Format categories for prompt
    categories_formatted = "\n".join([f"-Name: {name} Description: {desc}" for name, desc in categories_dict.items()])
    
    # Create prompt with format instructions
    prompt = PromptTemplate(
        template=template,
        input_variables=["text", "categories"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Generate the prompt text
    prompt_text = prompt.format(
        text=post['text'],
        categories=categories_formatted
    )
    
    return prompt_text, parser

def categorize_post(post, categories_dict):
    """
    Categorize a single post.
    This function is maintained for backward compatibility.
    """
    prompt_text, parser = format_prompt(post, categories_dict)
    
    # Make the API call
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_text}],
        response_format={"type": "json_object"}  # Explicitly request JSON response
    )
    
    # Extract the content from the response
    response_content = response.choices[0].message.content
    
    try:
        # First try to parse directly with the LangChain parser
        parsed_response = parser.parse(response_content)
        return parsed_response.model_dump()
    except Exception as e:
        # Fallback: try to manually extract JSON if parser fails
        try:
            # Find JSON in the response if it's surrounded by other text
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                parsed_data = json.loads(json_str)
                
                # Ensure output matches our expected format
                if "categories" not in parsed_data:
                    return {"categories": []}
                return parsed_data
            else:
                return {"categories": []}
        except json.JSONDecodeError:
            # If all parsing attempts fail, return empty categories
            print(f"Failed to parse response: {response_content}")
            return {"categories": []}

def format_batch_prompt(posts, categories_dict):
    """
    Format a prompt for batch categorization of multiple posts.
    
    Args:
        posts (list): List of post dictionaries containing 'id' and 'text' keys
        categories_dict (dict): Dictionary mapping category names to descriptions
    
    Returns:
        tuple: (formatted prompt text, None)
    """
    # Format categories
    categories_formatted = "\n".join([f"Name: '{name}', Description: '{desc}'" for name, desc in categories_dict.items()])
    
    # Create a list of posts for the prompt
    posts_formatted = "\n\n".join([f"Post ID: {post['id']}\nText: \"{post['text']}\"" for post in posts])
    
    print(f'\nFor Categorization\nCategories : {categories_formatted}\n')
    
    # Create the prompt
    template = """
    You are an expert content categorizer. I need you to analyze multiple posts and assign relevant categories to each post.

    Here are the posts to categorize:
    {posts}
    
    Here are the available categories:
    {categories}
    
    For each post, determine which categories the post belongs to based on its content.
    You have to only include those categories that are given in the list of categories. Don't make category from your own. The category name should be same as given in the list of categories.
    Only include categories where there's a clear match based on the category description.
    A post can belong to multiple categories or none at all.
    
    Provide your output as a JSON object where each key is a post ID and the value is an array of category names. Tha category names should be a complete name as given in the list of categories.
    For posts that don't belong to any category, use an empty array.
    
    Example output format:
    {{
        "1234567890": ["Cat 1", "Cat 2"],
        "9876543210": ["Cat 1"],
        "5555555555": []
    }}
    
    Remember to use the exact category names as listed. Your response should contain only the JSON object.
    """
    
    # Format the prompt
    prompt_text = template.format(
        posts=posts_formatted,
        categories=categories_formatted
    )
    
    return prompt_text, None

def categorize_posts_batch(posts, categories_dict):
    """
    Categorize multiple posts in a single API call.
    
    Args:
        posts (list): List of post dictionaries
        categories_dict (dict): Dictionary mapping category names to descriptions
    
    Returns:
        dict: Dictionary mapping post IDs to lists of categories
    """
    prompt_text, _ = format_batch_prompt(posts, categories_dict)
    
    # Make the API call
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Using the same model as the single post categorization
        messages=[{"role": "user", "content": prompt_text}],
        response_format={"type": "json_object"}  # Explicitly request JSON response
    )
    
    # Extract the content from the response
    response_content = response.choices[0].message.content
    
    try:
        # Try to parse the JSON response
        # Find JSON in the response if it's surrounded by other text
        json_start = response_content.find('{')
        json_end = response_content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_content[json_start:json_end]
            result = json.loads(json_str)
            
            # Convert all post IDs to strings to ensure correct matching
            result = {str(post_id): categories for post_id, categories in result.items()}
            
            return result
        else:
            print(f"Failed to find JSON in response: {response_content}")
            return {}
    except json.JSONDecodeError as e:
        print(f"Failed to parse response as JSON: {e}\nResponse: {response_content}")
        return {}
    except Exception as e:
        print(f"Unexpected error processing response: {e}\nResponse: {response_content}")
        return {}

# Example usage
if __name__ == "__main__":
    # Example 1: Single post categorization
    post1 = {"id": "12345", "text": "I love the new iPhone camera quality! The photos are stunning."}
    
    # Example 2: Post that doesn't match any category
    post2 = {"id": "67890", "text": "Good morning everyone! Hope you have a nice day."}
    
    # Example 3: For batch processing
    posts = [post1, post2]
    
    categories_dict = {
        "Technology": "Posts about gadgets, software, or technical topics",
        "Photography": "Posts about taking photos or camera equipment",
        "Shopping": "Posts about purchasing products or services"
    }
    
    print("Example 1 (Single post categorization):")
    result1 = categorize_post(post1, categories_dict)
    print(json.dumps(result1, indent=2))
    
    print("\nExample 2 (Batch categorization):")
    batch_result = categorize_posts_batch(posts, categories_dict)
    print(json.dumps(batch_result, indent=2))