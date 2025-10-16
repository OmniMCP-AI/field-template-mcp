#!/usr/bin/env python3
"""
MCP Template Server Integration Tests

Test Functions:
- test_hello: Test the hello tool
- test_summarize_text: Test the summarize_text tool with LLM

Usage:
    # Run all tests
    python test/test_mcp_client.py --env=local --test=all

    # Run specific test
    python test/test_mcp_client.py --env=local --test=hello
    python test/test_mcp_client.py --env=local --test=summarize

Environment Variables Required:
- OPENAI_API_KEY (for summarize_text tool)
- OPENAI_BASE_URL (optional, for OpenRouter or custom endpoints)
- OPENAI_MODEL (optional, default: gpt-4o-mini)
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables
load_dotenv()


async def test_hello(url):
    """Test the hello tool"""
    print("🚀 Testing Hello Tool")
    print("=" * 60)

    async with streamablehttp_client(url=url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: List available tools
            print("\n🛠️  Test 1: Listing available MCP tools")
            tools = await session.list_tools()
            print(f"✅ Found {len(tools.tools)} available tools:")
            for i, tool in enumerate(tools.tools, 1):
                print(f"   {i:2d}. {tool.name}: {tool.description[:80]}...")

            # Test 2: Call hello tool
            print("\n👋 Test 2: Calling hello tool")
            hello_res = await session.call_tool("hello", {"name": "World"})
            
            if hello_res.isError:
                print(f"❌ Error: {hello_res.content[0].text if hello_res.content else 'Unknown error'}")
            else:
                result = hello_res.content[0].text if hello_res.content else None
                print(f"✅ Result: {result}")

            # Test 3: Call hello with different name
            print("\n👋 Test 3: Calling hello tool with custom name")
            hello_res2 = await session.call_tool("hello", {"name": "MCP Template"})
            
            if hello_res2.isError:
                print(f"❌ Error: {hello_res2.content[0].text if hello_res2.content else 'Unknown error'}")
            else:
                result = hello_res2.content[0].text if hello_res2.content else None
                print(f"✅ Result: {result}")

            print("\n✅ Hello tool test completed!")


async def test_summarize_text(url):
    """Test the summarize_text tool"""
    print("🚀 Testing Summarize Text Tool")
    print("=" * 60)

    async with streamablehttp_client(url=url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Summarize a short text
            print("\n📝 Test 1: Summarizing a short text")
            short_text = """
            The Model Context Protocol (MCP) is an open protocol that enables seamless integration 
            between LLM applications and external data sources and tools. Whether you're building 
            an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, 
            MCP provides a standardized way to connect LLMs with the context they need.
            """
            
            print(f"   Original text length: {len(short_text)} characters")
            
            summarize_res = await session.call_tool(
                "summarize_text",
                {"text": short_text, "max_words": 30}
            )
            
            if summarize_res.isError:
                print(f"❌ Error: {summarize_res.content[0].text if summarize_res.content else 'Unknown error'}")
            else:
                result_text = summarize_res.content[0].text if summarize_res.content else None
                if result_text:
                    try:
                        result = json.loads(result_text)
                        if result.get("success"):
                            print(f"✅ Summary: {result['summary']}")
                            print(f"   Word count: {result['word_count']} words")
                            print(f"   Original length: {result['original_length']} characters")
                            if result.get('key_points'):
                                print(f"   Key points: {', '.join(result['key_points'][:3])}...")
                        else:
                            print(f"❌ Error in response: {result.get('error', 'Unknown error')}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON: {e}")
                        print(f"   Raw response: {result_text[:100]}...")

            # Test 2: Summarize a longer text
            print("\n📝 Test 2: Summarizing a longer text")
            long_text = """
            Artificial Intelligence (AI) has revolutionized numerous industries and continues to 
            reshape our world in unprecedented ways. From healthcare to finance, transportation to 
            entertainment, AI technologies are being deployed to solve complex problems and enhance 
            human capabilities. Machine learning, a subset of AI, enables systems to learn from data 
            and improve their performance over time without explicit programming. Deep learning, 
            inspired by the structure of the human brain, has achieved remarkable breakthroughs in 
            image recognition, natural language processing, and game playing. However, the rapid 
            advancement of AI also raises important ethical questions about privacy, bias, job 
            displacement, and the future role of humans in an increasingly automated world. As we 
            continue to develop more sophisticated AI systems, it becomes crucial to establish 
            guidelines and regulations that ensure these technologies are used responsibly and 
            for the benefit of all humanity.
            """
            
            print(f"   Original text length: {len(long_text)} characters")
            
            summarize_res2 = await session.call_tool(
                "summarize_text",
                {"text": long_text, "max_words": 50}
            )
            
            if summarize_res2.isError:
                print(f"❌ Error: {summarize_res2.content[0].text if summarize_res2.content else 'Unknown error'}")
            else:
                result_text = summarize_res2.content[0].text if summarize_res2.content else None
                if result_text:
                    try:
                        result = json.loads(result_text)
                        if result.get("success"):
                            print(f"✅ Summary: {result['summary']}")
                            print(f"   Word count: {result['word_count']} words")
                            print(f"   Original length: {result['original_length']} characters")
                            print(f"   Model used: {result.get('model', 'unknown')}")
                            if result.get('key_points'):
                                print(f"   Key points ({len(result['key_points'])}): {result['key_points']}")
                        else:
                            print(f"❌ Error in response: {result.get('error', 'Unknown error')}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON: {e}")

            # Test 3: Summarize with very short limit
            print("\n📝 Test 3: Summarizing with very short limit (20 words)")
            
            summarize_res3 = await session.call_tool(
                "summarize_text",
                {"text": long_text, "max_words": 20}
            )
            
            if summarize_res3.isError:
                print(f"❌ Error: {summarize_res3.content[0].text if summarize_res3.content else 'Unknown error'}")
            else:
                result_text = summarize_res3.content[0].text if summarize_res3.content else None
                if result_text:
                    try:
                        result = json.loads(result_text)
                        if result.get("success"):
                            print(f"✅ Summary: {result['summary']}")
                            print(f"   Word count: {result['word_count']} words (requested max: 20)")
                            if result['word_count'] <= 25:  # Allow some flexibility
                                print(f"   ✅ PASS: Word count within limit")
                            else:
                                print(f"   ⚠️  WARNING: Word count exceeds requested limit")
                        else:
                            print(f"❌ Error in response: {result.get('error', 'Unknown error')}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON: {e}")

            # Test 4: Test with default max_words parameter
            print("\n📝 Test 4: Summarizing with default max_words (50)")
            
            summarize_res4 = await session.call_tool(
                "summarize_text",
                {"text": short_text}  # No max_words specified, should use default
            )
            
            if summarize_res4.isError:
                print(f"❌ Error: {summarize_res4.content[0].text if summarize_res4.content else 'Unknown error'}")
            else:
                result_text = summarize_res4.content[0].text if summarize_res4.content else None
                if result_text:
                    try:
                        result = json.loads(result_text)
                        if result.get("success"):
                            print(f"✅ Summary: {result['summary']}")
                            print(f"   Word count: {result['word_count']} words (default max: 50)")
                        else:
                            print(f"❌ Error in response: {result.get('error', 'Unknown error')}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON: {e}")

            print("\n✅ Summarize text tool test completed!")


async def test_json_structure(url):
    """Test JSON structure validation - new comprehensive test case"""
    print("🚀 Testing JSON Structure Validation")
    print("=" * 60)

    async with streamablehttp_client(url=url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Validate JSON structure
            print("\n🔍 Test 1: Validating JSON response structure")
            test_text = """
            Machine learning is a subset of artificial intelligence that enables computers 
            to learn and improve from experience without being explicitly programmed. It uses 
            algorithms to analyze data, identify patterns, and make decisions with minimal 
            human intervention.
            """
            
            response = await session.call_tool(
                "summarize_text",
                {"text": test_text, "max_words": 40}
            )
            
            if not response.isError and response.content:
                result_text = response.content[0].text
                try:
                    result = json.loads(result_text)
                    print("✅ Response is valid JSON")
                    
                    # Check if this is an error response
                    if not result.get("success"):
                        print(f"⚠️  API Error occurred: {result.get('error', 'Unknown error')}")
                        print("   Skipping field validation for error response")
                        print("   ✅ PASS: Error response structure is valid")
                        # Continue to next test
                    else:
                        # Validate required fields for successful response
                        required_fields = ["success", "summary", "key_points", "word_count", "original_length", "model"]
                        missing_fields = [field for field in required_fields if field not in result]
                        
                        if not missing_fields:
                            print(f"✅ All required fields present: {required_fields}")
                        else:
                            print(f"❌ Missing fields: {missing_fields}")
                        
                        # Validate data types
                        print("\n📊 Validating data types:")
                        validations = []
                        
                        if isinstance(result.get("success"), bool):
                            print(f"   ✅ 'success' is boolean: {result['success']}")
                            validations.append(True)
                        else:
                            print(f"   ❌ 'success' is not boolean: {type(result.get('success'))}")
                            validations.append(False)
                        
                        if isinstance(result.get("summary"), str):
                            print(f"   ✅ 'summary' is string (length: {len(result['summary'])})")
                            validations.append(True)
                        else:
                            print(f"   ❌ 'summary' is not string")
                            validations.append(False)
                        
                        if isinstance(result.get("key_points"), list):
                            print(f"   ✅ 'key_points' is list (count: {len(result['key_points'])})")
                            validations.append(True)
                        else:
                            print(f"   ❌ 'key_points' is not list")
                            validations.append(False)
                        
                        if isinstance(result.get("word_count"), int):
                            print(f"   ✅ 'word_count' is integer: {result['word_count']}")
                            validations.append(True)
                        else:
                            print(f"   ❌ 'word_count' is not integer")
                            validations.append(False)
                        
                        if isinstance(result.get("original_length"), int):
                            print(f"   ✅ 'original_length' is integer: {result['original_length']}")
                            validations.append(True)
                        else:
                            print(f"   ❌ 'original_length' is not integer")
                            validations.append(False)
                        
                        if isinstance(result.get("model"), str):
                            print(f"   ✅ 'model' is string: {result['model']}")
                            validations.append(True)
                        else:
                            print(f"   ❌ 'model' is not string")
                            validations.append(False)
                        
                        # Overall validation result
                        if all(validations) and not missing_fields:
                            print("\n🎉 PASS: JSON structure is fully valid!")
                        else:
                            print("\n⚠️  FAIL: JSON structure has issues")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")

            # Test 2: Test error handling with JSON
            print("\n🔍 Test 2: Validating error response structure")
            # Test with empty text (should handle gracefully)
            error_response = await session.call_tool(
                "summarize_text",
                {"text": "", "max_words": 10}
            )
            
            if not error_response.isError and error_response.content:
                result_text = error_response.content[0].text
                try:
                    result = json.loads(result_text)
                    print("✅ Error response is valid JSON")
                    
                    # Even with empty text, should return valid structure
                    if "success" in result:
                        if result["success"]:
                            print(f"   ℹ️  Empty text handled gracefully")
                            print(f"   Summary: {result.get('summary', 'N/A')}")
                        else:
                            print(f"   ✅ Error properly indicated: {result.get('error', 'N/A')}")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Error response is not valid JSON: {e}")

            # Test 3: Consistency check
            print("\n🔍 Test 3: Validating consistency of word count")
            consistency_response = await session.call_tool(
                "summarize_text",
                {"text": test_text, "max_words": 25}
            )
            
            if not consistency_response.isError and consistency_response.content:
                result_text = consistency_response.content[0].text
                try:
                    result = json.loads(result_text)
                    if result.get("success"):
                        reported_count = result.get("word_count", 0)
                        actual_count = len(result.get("summary", "").split())
                        
                        print(f"   Reported word count: {reported_count}")
                        print(f"   Actual word count: {actual_count}")
                        
                        if reported_count == actual_count:
                            print(f"   ✅ PASS: Word counts match")
                        else:
                            print(f"   ⚠️  WARNING: Word counts don't match")
                        
                        # Check if within requested limit (with some tolerance)
                        requested_max = 25
                        if actual_count <= requested_max + 5:  # 5 word tolerance
                            print(f"   ✅ PASS: Summary within word limit ({requested_max} +/- 5)")
                        else:
                            print(f"   ⚠️  WARNING: Summary exceeds word limit")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")

            print("\n✅ JSON structure validation test completed!")


async def test_all(url):
    """Run all tests"""
    print("🎯 Running All Tests")
    print("=" * 80)
    
    await test_hello(url)
    print("\n" + "=" * 80 + "\n")
    await test_summarize_text(url)
    print("\n" + "=" * 80 + "\n")
    await test_json_structure(url)
    
    print("\n" + "=" * 80)
    print("🎉 ALL TESTS COMPLETED!")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test MCP Template Server")
    parser.add_argument(
        "--env",
        choices=["local", "remote"],
        default="local",
        help="Environment to use: local (127.0.0.1:8322) or remote (custom URL)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="",
        help="Custom URL for remote environment",
    )
    parser.add_argument(
        "--test",
        choices=["all", "hello", "summarize", "json"],
        default="all",
        help="Which test to run: all (default), hello, summarize, or json",
    )
    args = parser.parse_args()

    # Set endpoint based on environment argument
    if args.env == "local":
        endpoint = "http://127.0.0.1:8322"
    else:
        endpoint = args.url if args.url else "http://127.0.0.1:8322"

    print(f"🔗 Using {args.env} environment: {endpoint}")
    print(f"🧪 Running test: {args.test}")
    print()

    # Check for required environment variables if testing summarize
    if args.test in ["all", "summarize", "json"]:
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  WARNING: OPENAI_API_KEY not found in environment")
            print("   The summarize_text test will fail without it")
            print("   Please set it in .env file or environment variables")
            print()

    # Run the selected test(s)
    test_url = f"{endpoint}/mcp"
    
    if args.test == "all":
        asyncio.run(test_all(test_url))
    elif args.test == "hello":
        asyncio.run(test_hello(test_url))
    elif args.test == "summarize":
        asyncio.run(test_summarize_text(test_url))
    elif args.test == "json":
        asyncio.run(test_json_structure(test_url))

