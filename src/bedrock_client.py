"""AWS Bedrock Client Wrapper"""

import boto3
import json
import os
import logging

logger = logging.getLogger(__name__)

class BedrockClient:
    """Wrapper for AWS Bedrock Runtime"""

    def __init__(self, region_name: str = None, model_id: str = None):
        self.region_name = region_name or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.model_id = model_id or os.getenv(
            'BEDROCK_MODEL',
            'anthropic.claude-3-5-haiku-20241022-v1:0'
        )

        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region_name
        )
        logger.info(f"Bedrock client initialized: {self.model_id}")

    def invoke(self, messages: list, system: str = None, max_tokens: int = 4000, temperature: float = 0.7) -> dict:
        """Invoke Claude model on Bedrock"""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        if system:
            body["system"] = system

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )

        response_body = json.loads(response['body'].read())

        return {
            'content': response_body['content'][0]['text'],
            'usage': response_body['usage'],
            'stop_reason': response_body.get('stop_reason', 'end_turn')
        }
