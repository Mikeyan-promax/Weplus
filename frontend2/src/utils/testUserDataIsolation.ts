// 用户数据隔离功能测试脚本
import { setUserData, getUserData, clearUserData, USER_DATA_TYPES } from './userDataManager';

interface TestUser {
  id: string;
  name: string;
}

interface TestResult {
  testName: string;
  passed: boolean;
  message: string;
}

// 模拟用户信息
const testUsers: TestUser[] = [
  { id: 'user1', name: '张三' },
  { id: 'user2', name: '李四' }
];

// 模拟getUserInfo函数
let currentTestUser: TestUser | null = null;

// 重写getUserInfo用于测试
const originalGetUserInfo = (window as any).getUserInfo;
(window as any).getUserInfo = () => currentTestUser;

export const runUserDataIsolationTests = (): TestResult[] => {
  const results: TestResult[] = [];
  
  try {
    // 测试1: 基本数据隔离
    results.push(testBasicDataIsolation());
    
    // 测试2: 聊天历史隔离
    results.push(testChatHistoryIsolation());
    
    // 测试3: 用户设置隔离
    results.push(testUserSettingsIsolation());
    
    // 测试4: 数据清理功能
    results.push(testDataClearing());
    
    // 测试5: 错误处理
    results.push(testErrorHandling());
    
  } catch (error) {
    results.push({
      testName: '测试执行异常',
      passed: false,
      message: `测试执行过程中发生异常: ${error}`
    });
  } finally {
    // 恢复原始getUserInfo函数
    (window as any).getUserInfo = originalGetUserInfo;
    
    // 清理测试数据
    cleanupTestData();
  }
  
  return results;
};

function testBasicDataIsolation(): TestResult {
  try {
    // 设置用户1的数据
    currentTestUser = testUsers[0];
    setUserData(USER_DATA_TYPES.USER_PREFERENCES, { theme: 'dark', language: 'zh' });
    
    // 设置用户2的数据
    currentTestUser = testUsers[1];
    setUserData(USER_DATA_TYPES.USER_PREFERENCES, { theme: 'light', language: 'en' });
    
    // 验证用户1的数据
    currentTestUser = testUsers[0];
    const user1Data = getUserData(USER_DATA_TYPES.USER_PREFERENCES);
    
    // 验证用户2的数据
    currentTestUser = testUsers[1];
    const user2Data = getUserData(USER_DATA_TYPES.USER_PREFERENCES);
    
    const passed = user1Data?.theme === 'dark' && 
                   user1Data?.language === 'zh' &&
                   user2Data?.theme === 'light' && 
                   user2Data?.language === 'en';
    
    return {
      testName: '基本数据隔离测试',
      passed,
      message: passed ? '用户数据成功隔离' : `数据隔离失败: user1=${JSON.stringify(user1Data)}, user2=${JSON.stringify(user2Data)}`
    };
  } catch (error) {
    return {
      testName: '基本数据隔离测试',
      passed: false,
      message: `测试失败: ${error}`
    };
  }
}

function testChatHistoryIsolation(): TestResult {
  try {
    // 用户1的聊天历史
    currentTestUser = testUsers[0];
    const user1Messages = [
      { id: '1', content: '用户1的消息1', role: 'user', timestamp: Date.now() },
      { id: '2', content: 'AI回复1', role: 'assistant', timestamp: Date.now() }
    ];
    setUserData(USER_DATA_TYPES.CHAT_HISTORY, user1Messages);
    
    // 用户2的聊天历史
    currentTestUser = testUsers[1];
    const user2Messages = [
      { id: '3', content: '用户2的消息1', role: 'user', timestamp: Date.now() },
      { id: '4', content: 'AI回复2', role: 'assistant', timestamp: Date.now() }
    ];
    setUserData(USER_DATA_TYPES.CHAT_HISTORY, user2Messages);
    
    // 验证隔离
    currentTestUser = testUsers[0];
    const retrievedUser1Messages = getUserData(USER_DATA_TYPES.CHAT_HISTORY);
    
    currentTestUser = testUsers[1];
    const retrievedUser2Messages = getUserData(USER_DATA_TYPES.CHAT_HISTORY);
    
    const passed = retrievedUser1Messages?.length === 2 &&
                   retrievedUser2Messages?.length === 2 &&
                   retrievedUser1Messages[0].content === '用户1的消息1' &&
                   retrievedUser2Messages[0].content === '用户2的消息1';
    
    return {
      testName: '聊天历史隔离测试',
      passed,
      message: passed ? '聊天历史成功隔离' : '聊天历史隔离失败'
    };
  } catch (error) {
    return {
      testName: '聊天历史隔离测试',
      passed: false,
      message: `测试失败: ${error}`
    };
  }
}

function testUserSettingsIsolation(): TestResult {
  try {
    // 用户1的设置
    currentTestUser = testUsers[0];
    const user1Settings = {
      messageNotifications: true,
      activityReminders: false,
      emailNotifications: true,
      profileVisibility: true,
      dataSharing: false
    };
    setUserData(USER_DATA_TYPES.NOTIFICATION_SETTINGS, user1Settings);
    
    // 用户2的设置
    currentTestUser = testUsers[1];
    const user2Settings = {
      messageNotifications: false,
      activityReminders: true,
      emailNotifications: false,
      profileVisibility: false,
      dataSharing: true
    };
    setUserData(USER_DATA_TYPES.NOTIFICATION_SETTINGS, user2Settings);
    
    // 验证隔离
    currentTestUser = testUsers[0];
    const retrievedUser1Settings = getUserData(USER_DATA_TYPES.NOTIFICATION_SETTINGS);
    
    currentTestUser = testUsers[1];
    const retrievedUser2Settings = getUserData(USER_DATA_TYPES.NOTIFICATION_SETTINGS);
    
    const passed = retrievedUser1Settings?.messageNotifications === true &&
                   retrievedUser1Settings?.activityReminders === false &&
                   retrievedUser2Settings?.messageNotifications === false &&
                   retrievedUser2Settings?.activityReminders === true;
    
    return {
      testName: '用户设置隔离测试',
      passed,
      message: passed ? '用户设置成功隔离' : '用户设置隔离失败'
    };
  } catch (error) {
    return {
      testName: '用户设置隔离测试',
      passed: false,
      message: `测试失败: ${error}`
    };
  }
}

function testDataClearing(): TestResult {
  try {
    // 设置测试数据
    currentTestUser = testUsers[0];
    setUserData(USER_DATA_TYPES.USER_PREFERENCES, { test: 'data' });
    setUserData(USER_DATA_TYPES.CHAT_HISTORY, [{ id: '1', content: 'test', role: 'user', timestamp: Date.now() }]);
    
    // 清理数据
    clearUserData();
    
    // 验证数据已清理
    const preferences = getUserData(USER_DATA_TYPES.USER_PREFERENCES);
    const chatHistory = getUserData(USER_DATA_TYPES.CHAT_HISTORY);
    
    const passed = preferences === null && chatHistory === null;
    
    return {
      testName: '数据清理功能测试',
      passed,
      message: passed ? '数据清理功能正常' : '数据清理功能异常'
    };
  } catch (error) {
    return {
      testName: '数据清理功能测试',
      passed: false,
      message: `测试失败: ${error}`
    };
  }
}

function testErrorHandling(): TestResult {
  try {
    // 测试无用户情况
    currentTestUser = null;
    
    let errorCaught = false;
    try {
      setUserData(USER_DATA_TYPES.USER_PREFERENCES, { test: 'data' });
    } catch (error) {
      errorCaught = true;
    }
    
    const passed = errorCaught;
    
    return {
      testName: '错误处理测试',
      passed,
      message: passed ? '错误处理正常' : '错误处理异常'
    };
  } catch (error) {
    return {
      testName: '错误处理测试',
      passed: false,
      message: `测试失败: ${error}`
    };
  }
}

function cleanupTestData(): void {
  try {
    // 清理所有测试用户的数据
    testUsers.forEach(user => {
      currentTestUser = user;
      clearUserData();
    });
  } catch (error) {
    console.warn('清理测试数据失败:', error);
  }
}

// 在控制台中运行测试的便捷函数
export const runTests = () => {
  console.log('🧪 开始用户数据隔离测试...');
  const results = runUserDataIsolationTests();
  
  console.log('\n📊 测试结果:');
  results.forEach((result, index) => {
    const status = result.passed ? '✅' : '❌';
    console.log(`${index + 1}. ${status} ${result.testName}: ${result.message}`);
  });
  
  const passedCount = results.filter(r => r.passed).length;
  const totalCount = results.length;
  
  console.log(`\n🎯 总结: ${passedCount}/${totalCount} 个测试通过`);
  
  if (passedCount === totalCount) {
    console.log('🎉 所有测试通过！用户数据隔离功能正常工作。');
  } else {
    console.log('⚠️ 部分测试失败，请检查用户数据隔离功能。');
  }
  
  return results;
};

// 将测试函数暴露到全局，方便在浏览器控制台中调用
(window as any).runUserDataIsolationTests = runTests;