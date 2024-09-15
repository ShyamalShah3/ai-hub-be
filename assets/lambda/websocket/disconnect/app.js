const { DynamoDBClient, PutItemCommand } = require('@aws-sdk/client-dynamodb');

const client = new DynamoDBClient({
  region: process.env.REGION
});

exports.handler = async event => {

  const params = {
    TableName: process.env.TABLE_NAME,
    Item: {
      connectionId: {
        S: event.requestContext.connectionId  
      }
    }
  };

  try {
    await client.send(new PutItemCommand(params));
  } catch (err) {
    return { 
      statusCode: 500,
      body: `Failed to connect: ${err.message}`
    };
  }

  return {
    statusCode: 200,
    body: 'Connected'
  };
};
