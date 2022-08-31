<Query Kind="Statements">
  <Reference>&lt;NuGet&gt;\google.protobuf\3.21.5\lib\net5.0\Google.Protobuf.dll</Reference>
  <Namespace>Google.Protobuf</Namespace>
  <Namespace>Google.Protobuf.WellKnownTypes</Namespace>
  <Namespace>System.Text.Json</Namespace>
  <Namespace>System.Text.Json.Nodes</Namespace>
</Query>

string[] keys = new string[] {"hello", "world", "!"};
JsonArray jsonArray = new JsonArray();
foreach(var key in keys)
{
    jsonArray.Add(key);
}

string ret = $"{{\"result\": {jsonArray.ToJsonString()}}}";
Console.WriteLine(ret);

Console.WriteLine(@"{""result"": ""None""}");