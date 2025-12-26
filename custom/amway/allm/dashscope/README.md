### 正常输出结果
```txt
{
	'output': {
		'finish_reason': 'stop',
		'text': '广州是一座历史悠久的城市，拥有许多有趣的景点。其中最著名的有：珠江夜游、花城广场、海心沙、白云山、越秀公园、北京路步行街等。此外，还有许多非常棒的餐厅和美食可以尝试，例如牛肉粉、烧鹅、海鲜粥等等。'
	},
	'usage': {
		'total_tokens': 68,
		'output_tokens': 64,
		'input_tokens': 4
	},
	'request_id': '76f42569-2a40-9ae3-babc-33982d89f77e'
}
```

### 异常输出结果
```txt
{
  'code': 'DataInspectionFailed', 
  'message': 'Output data may contain inappropriate content.', 
  'request_id': 'bd89a98d-2fe6-9c96-9daa-9e7d2af9eeaa'
}
```