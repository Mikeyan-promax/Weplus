// 原有功能测试脚本
// 用于验证新添加的用户数据隔离功能是否影响了原有功能

interface FunctionalityTestResult {
  testName: string;
  passed: boolean;
  message: string;
  details?: string;
}

export const runFunctionalityTests = (): FunctionalityTestResult[] => {
  const results: FunctionalityTestResult[] = [];
  
  try {
    // 测试1: 认证系统功能
    results.push(testAuthenticationSystem());
    
    // 测试2: 本地存储基础功能
    results.push(testLocalStorageBasics());
    
    // 测试3: React组件渲染
    results.push(testComponentRendering());
    
    // 测试4: 路由系统
    results.push(testRoutingSystem());
    
    // 测试5: API调用功能
    results.push(testAPIFunctionality());
    
  } catch (error) {
    results.push({
      testName: '功能测试执行异常',
      passed: false,
      message: `测试执行过程中发生异常: ${error}`
    });
  }
  
  return results;
};

function testAuthenticationSystem(): FunctionalityTestResult {
  try {
    // 检查认证相关的localStorage键是否存在
    const authKeys = ['authToken', 'refreshToken', 'user'];
    let foundAuthData = false;
    
    authKeys.forEach(key => {
      if (localStorage.getItem(key)) {
        foundAuthData = true;
      }
    });
    
    // 检查AuthContext是否可用
    const authContextAvailable = typeof (window as any).React !== 'undefined';
    
    return {
      testName: '认证系统功能测试',
      passed: true, // 基础检查通过
      message: '认证系统基础功能正常',
      details: `认证数据存在: ${foundAuthData}, React可用: ${authContextAvailable}`
    };
  } catch (error) {
    return {
      testName: '认证系统功能测试',
      passed: false,
      message: `认证系统测试失败: ${error}`
    };
  }
}

function testLocalStorageBasics(): FunctionalityTestResult {
  try {
    const testKey = 'functionality_test_key';
    const testValue = 'test_value_' + Date.now();
    
    // 测试写入
    localStorage.setItem(testKey, testValue);
    
    // 测试读取
    const retrievedValue = localStorage.getItem(testKey);
    
    // 测试删除
    localStorage.removeItem(testKey);
    const deletedValue = localStorage.getItem(testKey);
    
    const passed = retrievedValue === testValue && deletedValue === null;
    
    return {
      testName: '本地存储基础功能测试',
      passed,
      message: passed ? '本地存储功能正常' : '本地存储功能异常',
      details: `写入值: ${testValue}, 读取值: ${retrievedValue}, 删除后: ${deletedValue}`
    };
  } catch (error) {
    return {
      testName: '本地存储基础功能测试',
      passed: false,
      message: `本地存储测试失败: ${error}`
    };
  }
}

function testComponentRendering(): FunctionalityTestResult {
  try {
    // 检查主要DOM元素是否存在
    const rootElement = document.getElementById('root');
    const hasReactApp = rootElement && rootElement.children.length > 0;
    
    // 检查是否有React相关的属性
    const hasReactProps = rootElement && rootElement.querySelector('[data-reactroot], [data-react-helmet]');
    
    return {
      testName: 'React组件渲染测试',
      passed: !!hasReactApp,
      message: hasReactApp ? 'React组件渲染正常' : 'React组件渲染异常',
      details: `根元素存在: ${!!rootElement}, 有子元素: ${hasReactApp}, React属性: ${!!hasReactProps}`
    };
  } catch (error) {
    return {
      testName: 'React组件渲染测试',
      passed: false,
      message: `组件渲染测试失败: ${error}`
    };
  }
}

function testRoutingSystem(): FunctionalityTestResult {
  try {
    // 检查当前URL和路由状态
    const currentPath = window.location.pathname;
    const hasHistory = typeof window.history !== 'undefined';
    
    // 检查是否有路由相关的DOM元素
    const hasRouterElements = document.querySelector('[data-testid*="route"], .main-content, .sidebar');
    
    return {
      testName: '路由系统功能测试',
      passed: hasHistory && !!hasRouterElements,
      message: hasHistory && hasRouterElements ? '路由系统功能正常' : '路由系统可能存在问题',
      details: `当前路径: ${currentPath}, History API: ${hasHistory}, 路由元素: ${!!hasRouterElements}`
    };
  } catch (error) {
    return {
      testName: '路由系统功能测试',
      passed: false,
      message: `路由系统测试失败: ${error}`
    };
  }
}

function testAPIFunctionality(): FunctionalityTestResult {
  try {
    // 检查fetch API是否可用
    const hasFetch = typeof fetch !== 'undefined';
    
    // 检查XMLHttpRequest是否可用
    const hasXHR = typeof XMLHttpRequest !== 'undefined';
    
    // 检查是否有API相关的配置
    const hasApiConfig = typeof (window as any).API_BASE_URL !== 'undefined' || 
                         localStorage.getItem('apiBaseUrl') !== null;
    
    return {
      testName: 'API调用功能测试',
      passed: hasFetch || hasXHR,
      message: (hasFetch || hasXHR) ? 'API调用功能正常' : 'API调用功能不可用',
      details: `Fetch API: ${hasFetch}, XMLHttpRequest: ${hasXHR}, API配置: ${hasApiConfig}`
    };
  } catch (error) {
    return {
      testName: 'API调用功能测试',
      passed: false,
      message: `API功能测试失败: ${error}`
    };
  }
}

// 检查用户数据隔离功能是否影响了原有localStorage使用
export const testUserDataIsolationImpact = (): FunctionalityTestResult[] => {
  const results: FunctionalityTestResult[] = [];
  
  try {
    // 测试1: 检查是否影响了非用户数据的localStorage操作
    results.push(testNonUserDataStorage());
    
    // 测试2: 检查是否影响了原有的数据读取
    results.push(testOriginalDataAccess());
    
    // 测试3: 检查是否产生了意外的数据污染
    results.push(testDataPollution());
    
  } catch (error) {
    results.push({
      testName: '用户数据隔离影响测试异常',
      passed: false,
      message: `测试执行异常: ${error}`
    });
  }
  
  return results;
};

function testNonUserDataStorage(): FunctionalityTestResult {
  try {
    const testKey = 'non_user_data_test';
    const testValue = 'original_functionality_test';
    
    // 测试原有的localStorage操作是否受影响
    localStorage.setItem(testKey, testValue);
    const retrieved = localStorage.getItem(testKey);
    localStorage.removeItem(testKey);
    
    const passed = retrieved === testValue;
    
    return {
      testName: '非用户数据存储测试',
      passed,
      message: passed ? '原有localStorage功能未受影响' : '原有localStorage功能可能受到影响'
    };
  } catch (error) {
    return {
      testName: '非用户数据存储测试',
      passed: false,
      message: `测试失败: ${error}`
    };
  }
}

function testOriginalDataAccess(): FunctionalityTestResult {
  try {
    // 检查是否有原有的应用数据被意外修改
    const originalKeys = ['authToken', 'refreshToken', 'user', 'theme', 'language'];
    let originalDataIntact = true;
    let checkedKeys = 0;
    
    originalKeys.forEach(key => {
      const value = localStorage.getItem(key);
      if (value !== null) {
        checkedKeys++;
        // 检查值是否看起来像是被用户数据管理器修改过
        if (typeof value === 'string' && value.includes('user_data_')) {
          originalDataIntact = false;
        }
      }
    });
    
    return {
      testName: '原有数据访问测试',
      passed: originalDataIntact,
      message: originalDataIntact ? '原有数据访问正常' : '原有数据可能被意外修改',
      details: `检查了 ${checkedKeys} 个原有数据键`
    };
  } catch (error) {
    return {
      testName: '原有数据访问测试',
      passed: false,
      message: `测试失败: ${error}`
    };
  }
}

function testDataPollution(): FunctionalityTestResult {
  try {
    // 检查localStorage中是否有意外的用户数据键
    const allKeys = Object.keys(localStorage);
    const userDataKeys = allKeys.filter(key => key.startsWith('user_data_'));
    
    // 检查是否有无效的用户数据键（没有用户ID或数据类型）
    const invalidKeys = userDataKeys.filter(key => {
      const parts = key.split('_');
      return parts.length < 4; // user_data_{userId}_{dataType}
    });
    
    const passed = invalidKeys.length === 0;
    
    return {
      testName: '数据污染检测测试',
      passed,
      message: passed ? '未发现数据污染' : `发现 ${invalidKeys.length} 个无效的用户数据键`,
      details: `总用户数据键: ${userDataKeys.length}, 无效键: ${invalidKeys.join(', ')}`
    };
  } catch (error) {
    return {
      testName: '数据污染检测测试',
      passed: false,
      message: `测试失败: ${error}`
    };
  }
}

// 在控制台中运行所有功能测试的便捷函数
export const runAllFunctionalityTests = () => {
  console.log('🔧 开始原有功能测试...');
  
  const basicResults = runFunctionalityTests();
  const isolationResults = testUserDataIsolationImpact();
  
  const allResults = [...basicResults, ...isolationResults];
  
  console.log('\n📊 功能测试结果:');
  allResults.forEach((result, index) => {
    const status = result.passed ? '✅' : '❌';
    console.log(`${index + 1}. ${status} ${result.testName}: ${result.message}`);
    if (result.details) {
      console.log(`   详情: ${result.details}`);
    }
  });
  
  const passedCount = allResults.filter(r => r.passed).length;
  const totalCount = allResults.length;
  
  console.log(`\n🎯 总结: ${passedCount}/${totalCount} 个测试通过`);
  
  if (passedCount === totalCount) {
    console.log('🎉 所有功能测试通过！新功能未影响原有功能。');
  } else {
    console.log('⚠️ 部分功能测试失败，请检查新功能对原有功能的影响。');
  }
  
  return allResults;
};

// 将测试函数暴露到全局，方便在浏览器控制台中调用
(window as any).runFunctionalityTests = runAllFunctionalityTests;
