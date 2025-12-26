url = "https://restapi.amap.com/v3/geocode/geo?key={self.key}&address={cus_address}"
response = {
    'status': '1',
    'info': 'OK',
    'infocode': '10000',
    'count': '1',
    'geocodes': [{
        'formatted_address': '广东省广州市越秀区西门口',
        'country': '中国',
        'province': '广东省',
        'citycode': '020',
        'city': '广州市',
        'district': '越秀区',
        'township': [],
        'neighborhood': {
            'name': [],
            'type': []
        },
        'building': {
            'name': [],
            'type': []
        },
        'adcode': '440104',
        'street': [],
        'number': [],
        'location': '113.255120,23.125932',
        'level': '住宅区'
    }]
}

url_2 = "https://restapi.amap.com/v3/direction/driving?origin={origin}&destination={destination}&key={self.key}"
response_2 = {
    'status': '1',
    'info': 'OK',
    'infocode': '10000',
    'count': '1',
    'route': {
        'origin': '113.255120,23.125932',
        'destination': '113.264499,23.130061',
        'taxi_cost': '10',
        'paths': [{
            'distance': '2467',
            'duration': '427',
            'strategy': '速度最快',
            'tolls': '0',
            'toll_distance': '0',
            'steps': [{
                'instruction': '向西行驶57米右转',
                'orientation': '西',
                'distance': '57',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '20',
                'polyline': '113.255122,23.125931;113.255122,23.126021;113.255084,23.126075;113.255041,23.126097;113.254848,23.126102;113.254693,23.126102',
                'action': '右转',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '42',
                    'status': '未知',
                    'polyline': '113.255122,23.125931;113.255122,23.126021;113.255084,23.126075;113.255041,23.126097;113.254848,23.126102'
                }, {
                    'lcode': [],
                    'distance': '15',
                    'status': '未知',
                    'polyline': '113.254848,23.126102;113.254693,23.126102'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '沿人民北路向北行驶554米向右前方行驶',
                'orientation': '北',
                'road': '人民北路',
                'distance': '554',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '113',
                'polyline': '113.254693,23.126102;113.254698,23.12622;113.254762,23.12717;113.254843,23.127985;113.254859,23.128328;113.254853,23.128945;113.254853,23.129036;113.254864,23.129224;113.254875,23.129637;113.254886,23.129884;113.254864,23.130254;113.254843,23.130453;113.254784,23.130726;113.254768,23.130801;113.254682,23.131123',
                'action': '向右前方行驶',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '209',
                    'status': '畅通',
                    'polyline': '113.254693,23.126102;113.254698,23.12622;113.254762,23.12717;113.254843,23.127985'
                }, {
                    'lcode': [],
                    'distance': '37',
                    'status': '畅通',
                    'polyline': '113.254843,23.127985;113.254859,23.128328'
                }, {
                    'lcode': [],
                    'distance': '68',
                    'status': '畅通',
                    'polyline': '113.254859,23.128328;113.254853,23.128945'
                }, {
                    'lcode': [],
                    'distance': '9',
                    'status': '畅通',
                    'polyline': '113.254853,23.128945;113.254853,23.129036'
                }, {
                    'lcode': [],
                    'distance': '21',
                    'status': '畅通',
                    'polyline': '113.254853,23.129036;113.254864,23.129224'
                }, {
                    'lcode': [],
                    'distance': '45',
                    'status': '畅通',
                    'polyline': '113.254864,23.129224;113.254875,23.129637'
                }, {
                    'lcode': [],
                    'distance': '68',
                    'status': '畅通',
                    'polyline': '113.254875,23.129637;113.254886,23.129884;113.254864,23.130254'
                }, {
                    'lcode': [],
                    'distance': '22',
                    'status': '畅通',
                    'polyline': '113.254864,23.130254;113.254843,23.130453'
                }, {
                    'lcode': [],
                    'distance': '30',
                    'status': '畅通',
                    'polyline': '113.254843,23.130453;113.254784,23.130726'
                }, {
                    'lcode': [],
                    'distance': '8',
                    'status': '畅通',
                    'polyline': '113.254784,23.130726;113.254768,23.130801'
                }, {
                    'lcode': [],
                    'distance': '37',
                    'status': '畅通',
                    'polyline': '113.254768,23.130801;113.254682,23.131123'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '沿人民北路辅路向北行驶128米向右前方行驶',
                'orientation': '北',
                'road': '人民北路辅路',
                'distance': '128',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '26',
                'polyline': '113.254682,23.131123;113.254698,23.131332;113.254591,23.131821;113.254575,23.13188;113.254483,23.132185;113.254414,23.132239',
                'action': '向右前方行驶',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '78',
                    'status': '畅通',
                    'polyline': '113.254682,23.131123;113.254698,23.131332;113.254591,23.131821'
                }, {
                    'lcode': [],
                    'distance': '6',
                    'status': '畅通',
                    'polyline': '113.254591,23.131821;113.254575,23.13188'
                }, {
                    'lcode': [],
                    'distance': '44',
                    'status': '畅通',
                    'polyline': '113.254575,23.13188;113.254483,23.132185;113.254414,23.132239'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '沿人民北路途径东风西路向东北行驶46米右转',
                'orientation': '东北',
                'road': '人民北路',
                'distance': '46',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '14',
                'polyline': '113.254414,23.132239;113.254456,23.132336;113.25451,23.132459;113.254612,23.132615',
                'action': '右转',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '11',
                    'status': '畅通',
                    'polyline': '113.254414,23.132239;113.254456,23.132336'
                }, {
                    'lcode': [],
                    'distance': '35',
                    'status': '畅通',
                    'polyline': '113.254456,23.132336;113.25451,23.132459;113.254612,23.132615'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '沿东风西路向东行驶233米靠左进入左岔路',
                'orientation': '东',
                'road': '东风西路',
                'distance': '233',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '18',
                'polyline': '113.254612,23.132615;113.255148,23.132555;113.255326,23.132539;113.255508,23.132518;113.256318,23.132432;113.25679,23.132384;113.256903,23.132373',
                'action': '靠左',
                'assistant_action': '进入左岔路',
                'tmcs': [{
                    'lcode': [],
                    'distance': '55',
                    'status': '畅通',
                    'polyline': '113.254612,23.132615;113.255148,23.132555'
                }, {
                    'lcode': [],
                    'distance': '17',
                    'status': '畅通',
                    'polyline': '113.255148,23.132555;113.255326,23.132539'
                }, {
                    'lcode': [],
                    'distance': '19',
                    'status': '畅通',
                    'polyline': '113.255326,23.132539;113.255508,23.132518'
                }, {
                    'lcode': [],
                    'distance': '83',
                    'status': '畅通',
                    'polyline': '113.255508,23.132518;113.256318,23.132432'
                }, {
                    'lcode': [],
                    'distance': '48',
                    'status': '畅通',
                    'polyline': '113.256318,23.132432;113.25679,23.132384'
                }, {
                    'lcode': [],
                    'distance': '11',
                    'status': '畅通',
                    'polyline': '113.25679,23.132384;113.256903,23.132373'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '沿东风西路向东行驶490米靠左沿主路行驶',
                'orientation': '东',
                'road': '东风西路',
                'distance': '490',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '29',
                'polyline': '113.256903,23.132373;113.257037,23.132389;113.257503,23.132368;113.259027,23.132196;113.260186,23.131992;113.260347,23.131955;113.26047,23.13188;113.261623,23.131713',
                'action': '靠左',
                'assistant_action': '沿主路行驶',
                'tmcs': [{
                    'lcode': [],
                    'distance': '371',
                    'status': '畅通',
                    'polyline': '113.256903,23.132373;113.257037,23.132389;113.257503,23.132368;113.259027,23.132196;113.260186,23.131992;113.260347,23.131955;113.26047,23.13188'
                }, {
                    'lcode': [],
                    'distance': '119',
                    'status': '畅通',
                    'polyline': '113.26047,23.13188;113.261623,23.131713'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '沿东风西路途径东风中路向东行驶407米右转',
                'orientation': '东',
                'road': '东风西路',
                'distance': '407',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '40',
                'polyline': '113.261623,23.131713;113.262138,23.131638;113.262745,23.131552;113.263302,23.131493;113.263388,23.131488;113.264064,23.13145;113.264568,23.131424;113.265019,23.131402;113.265089,23.131397;113.265598,23.13137',
                'action': '右转',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '53',
                    'status': '畅通',
                    'polyline': '113.261623,23.131713;113.262138,23.131638'
                }, {
                    'lcode': [],
                    'distance': '129',
                    'status': '畅通',
                    'polyline': '113.262138,23.131638;113.262745,23.131552;113.263302,23.131493;113.263388,23.131488'
                }, {
                    'lcode': [],
                    'distance': '69',
                    'status': '畅通',
                    'polyline': '113.263388,23.131488;113.264064,23.13145'
                }, {
                    'lcode': [],
                    'distance': '51',
                    'status': '畅通',
                    'polyline': '113.264064,23.13145;113.264568,23.131424'
                }, {
                    'lcode': [],
                    'distance': '46',
                    'status': '畅通',
                    'polyline': '113.264568,23.131424;113.265019,23.131402'
                }, {
                    'lcode': [],
                    'distance': '7',
                    'status': '畅通',
                    'polyline': '113.265019,23.131402;113.265089,23.131397'
                }, {
                    'lcode': [],
                    'distance': '52',
                    'status': '畅通',
                    'polyline': '113.265089,23.131397;113.265598,23.13137'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '沿吉祥路向南行驶296米右转',
                'orientation': '南',
                'road': '吉祥路',
                'distance': '296',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '92',
                'polyline': '113.265598,23.13137;113.265636,23.131295;113.265663,23.131193;113.265668,23.131091;113.265641,23.130828;113.265577,23.130185;113.26555,23.129938;113.265491,23.129111;113.265491,23.12901;113.26547,23.128688',
                'action': '右转',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '61',
                    'status': '畅通',
                    'polyline': '113.265598,23.13137;113.265636,23.131295;113.265663,23.131193;113.265668,23.131091;113.265641,23.130828'
                }, {
                    'lcode': [],
                    'distance': '71',
                    'status': '畅通',
                    'polyline': '113.265641,23.130828;113.265577,23.130185'
                }, {
                    'lcode': [],
                    'distance': '27',
                    'status': '畅通',
                    'polyline': '113.265577,23.130185;113.26555,23.129938'
                }, {
                    'lcode': [],
                    'distance': '102',
                    'status': '畅通',
                    'polyline': '113.26555,23.129938;113.265491,23.129111;113.265491,23.12901'
                }, {
                    'lcode': [],
                    'distance': '35',
                    'status': '畅通',
                    'polyline': '113.265491,23.12901;113.26547,23.128688'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '沿府前路向西行驶54米右转',
                'orientation': '西',
                'road': '府前路',
                'distance': '54',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '18',
                'polyline': '113.26547,23.128688;113.264939,23.12872',
                'action': '右转',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '54',
                    'status': '未知',
                    'polyline': '113.26547,23.128688;113.264939,23.12872'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '向北行驶103米靠右',
                'orientation': '北',
                'distance': '103',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '22',
                'polyline': '113.264939,23.12872;113.264939,23.129085;113.264944,23.129653',
                'action': '靠右',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '40',
                    'status': '未知',
                    'polyline': '113.264939,23.12872;113.264939,23.129085'
                }, {
                    'lcode': [],
                    'distance': '63',
                    'status': '未知',
                    'polyline': '113.264939,23.129085;113.264944,23.129653'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '向北行驶67米左转',
                'orientation': '北',
                'distance': '67',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '25',
                'polyline': '113.264944,23.129653;113.264837,23.129782;113.264821,23.129841;113.264831,23.130238',
                'action': '左转',
                'assistant_action': [],
                'tmcs': [{
                    'lcode': [],
                    'distance': '24',
                    'status': '未知',
                    'polyline': '113.264944,23.129653;113.264837,23.129782;113.264821,23.129841'
                }, {
                    'lcode': [],
                    'distance': '43',
                    'status': '未知',
                    'polyline': '113.264821,23.129841;113.264831,23.130238'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }, {
                'instruction': '向西行驶32米到达目的地',
                'orientation': '西',
                'distance': '32',
                'tolls': '0',
                'toll_distance': '0',
                'toll_road': [],
                'duration': '10',
                'polyline': '113.264831,23.130238;113.264523,23.130269',
                'action': [],
                'assistant_action': '到达目的地',
                'tmcs': [{
                    'lcode': [],
                    'distance': '32',
                    'status': '未知',
                    'polyline': '113.264831,23.130238;113.264523,23.130269'
                }],
                'cities': [{
                    'name': '广州市',
                    'citycode': '020',
                    'adcode': '440100',
                    'districts': [{
                        'name': '越秀区',
                        'adcode': '440104'
                    }]
                }]
            }],
            'restriction': '0',
            'traffic_lights': '6'
        }]
    }
}

url_3 = "https://restapi.amap.com/v3/weather/weatherInfo?city={city}&key={self.key}"
response_3 = {
    'status': '1',
    'count': '1',
    'info': 'OK',
    'infocode': '10000',
    'lives': [{
        'province': '广东',
        'city': '广州市',
        'adcode': '440100',
        'weather': '阴',
        'temperature': '26',
        'winddirection': '东南',
        'windpower': '≤3',
        'humidity': '95',
        'reporttime': '2024-06-16 08:00:24',
        'temperature_float': '26.0',
        'humidity_float': '95.0'
    }]
}
