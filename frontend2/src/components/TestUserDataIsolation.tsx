import React, { useState } from 'react';
import { runUserDataIsolationTests } from '../utils/testUserDataIsolation';
import AnimatedButton from './AnimatedButton';

interface TestResult {
  testName: string;
  passed: boolean;
  message: string;
}

const TestUserDataIsolation: React.FC = () => {
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunTests = async () => {
    setIsRunning(true);
    try {
      const results = runUserDataIsolationTests();
      setTestResults(results);
    } catch (error) {
      console.error('测试执行失败:', error);
      setTestResults([{
        testName: '测试执行异常',
        passed: false,
        message: `测试执行失败: ${error}`
      }]);
    } finally {
      setIsRunning(false);
    }
  };

  const passedCount = testResults.filter(r => r.passed).length;
  const totalCount = testResults.length;

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>🧪 用户数据隔离功能测试</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <AnimatedButton
          onClick={handleRunTests}
          disabled={isRunning}
          style={{
            backgroundColor: '#007bff',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '5px',
            cursor: isRunning ? 'not-allowed' : 'pointer'
          }}
        >
          {isRunning ? '测试运行中...' : '运行测试'}
        </AnimatedButton>
      </div>

      {testResults.length > 0 && (
        <div>
          <h3>📊 测试结果 ({passedCount}/{totalCount} 通过)</h3>
          
          <div style={{
            padding: '15px',
            borderRadius: '8px',
            backgroundColor: passedCount === totalCount ? '#d4edda' : '#f8d7da',
            border: `1px solid ${passedCount === totalCount ? '#c3e6cb' : '#f5c6cb'}`,
            marginBottom: '20px'
          }}>
            {passedCount === totalCount ? (
              <div style={{ color: '#155724' }}>
                🎉 <strong>所有测试通过！</strong> 用户数据隔离功能正常工作。
              </div>
            ) : (
              <div style={{ color: '#721c24' }}>
                ⚠️ <strong>部分测试失败</strong>，请检查用户数据隔离功能。
              </div>
            )}
          </div>

          <div style={{ display: 'grid', gap: '10px' }}>
            {testResults.map((result, index) => (
              <div
                key={index}
                style={{
                  padding: '12px',
                  borderRadius: '6px',
                  border: `1px solid ${result.passed ? '#c3e6cb' : '#f5c6cb'}`,
                  backgroundColor: result.passed ? '#f8fff9' : '#fff8f8'
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '5px'
                }}>
                  <span style={{ 
                    fontSize: '18px', 
                    marginRight: '8px' 
                  }}>
                    {result.passed ? '✅' : '❌'}
                  </span>
                  <strong style={{
                    color: result.passed ? '#155724' : '#721c24'
                  }}>
                    {result.testName}
                  </strong>
                </div>
                <div style={{
                  color: '#666',
                  fontSize: '14px',
                  marginLeft: '26px'
                }}>
                  {result.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h4>💡 测试说明</h4>
        <ul style={{ margin: '10px 0', paddingLeft: '20px' }}>
          <li><strong>基本数据隔离测试</strong>: 验证不同用户的基础数据是否相互独立</li>
          <li><strong>聊天历史隔离测试</strong>: 验证不同用户的聊天记录是否相互独立</li>
          <li><strong>用户设置隔离测试</strong>: 验证不同用户的个人设置是否相互独立</li>
          <li><strong>数据清理功能测试</strong>: 验证用户注销时数据是否正确清理</li>
          <li><strong>错误处理测试</strong>: 验证异常情况下的错误处理机制</li>
        </ul>
      </div>

      <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#e7f3ff', borderRadius: '8px' }}>
        <h4>🔧 手动测试建议</h4>
        <ol style={{ margin: '10px 0', paddingLeft: '20px' }}>
          <li>注册/登录用户A，发送几条AI聊天消息，修改个人设置</li>
          <li>注销用户A，注册/登录用户B</li>
          <li>检查用户B是否看不到用户A的聊天历史和设置</li>
          <li>用户B发送不同的消息，修改不同的设置</li>
          <li>重新登录用户A，验证数据是否保持不变</li>
        </ol>
      </div>
    </div>
  );
};

export default TestUserDataIsolation;