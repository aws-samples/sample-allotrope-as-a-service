#!/usr/bin/env node

/**
 * Test TypeScript to Python Strands Agent Integration
 */

const { spawn } = require('child_process');
const path = require('path');

// Simple UUID generator to avoid external dependency
function generateId() {
    return 'test-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

async function testIndividualAgent() {
    console.log('=== Testing Individual Python Agent ===\n');
    
    const fs = require('fs');
    const agentPath = path.join(__dirname, 'src', 'agents', 'strands-file-analysis-agent.py');
    const testInput = {
        filename: 'test.csv',
        file_content: 'Time,Value\n1,100\n2,200'
    };
    
    return new Promise((resolve) => {
        console.log('🔄 Calling Python file analysis agent directly...');
        console.log('📁 Agent path:', agentPath);
        
        // Write input to temp file
        const tempFile = path.join(__dirname, 'temp_input.json');
        fs.writeFileSync(tempFile, JSON.stringify(testInput));
        
        // Create a simple wrapper script
        const wrapperScript = `
import sys
import json

# Read input from temp file
with open('${tempFile.replace(/\\/g, '/')}', 'r') as f:
    input_data = json.load(f)

# Set sys.argv to simulate command line input
sys.argv = ['strands-file-analysis-agent.py', json.dumps(input_data)]

# Execute the agent script
exec(open('${agentPath.replace(/\\/g, '/')}').read())
`;
        
        const wrapperFile = path.join(__dirname, 'temp_wrapper.py');
        fs.writeFileSync(wrapperFile, wrapperScript);
        
        const python = spawn('python', [wrapperFile], {
            shell: true,
            cwd: __dirname
        });
        
        let stdout = '';
        let stderr = '';
        
        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        python.on('close', (code) => {
            // Clean up temp files
            try {
                fs.unlinkSync(tempFile);
                fs.unlinkSync(wrapperFile);
            } catch (e) {}
            
            if (code === 0) {
                try {
                    const result = JSON.parse(stdout);
                    console.log('✅ Direct agent call successful');
                    console.log('📊 Agent:', result.agent);
                    console.log('📁 Filename:', result.filename);
                    console.log('⏰ Timestamp:', result.timestamp);
                    console.log('🎯 Success:', result.success);
                } catch (error) {
                    console.log('❌ Failed to parse agent response');
                    console.log('Raw output:', stdout);
                }
            } else {
                console.log('❌ Agent failed with code:', code);
                console.log('Error output:', stderr);
                console.log('Standard output:', stdout);
            }
            resolve();
        });
        
        python.on('error', (error) => {
            console.log('💥 Failed to spawn Python agent:', error.message);
            resolve();
        });
    });
}

async function testConverterAgent() {
    console.log('\n=== Testing Converter Generation Agent ===\n');
    
    const agentPath = path.join(__dirname, 'src', 'agents', 'strands-converter-generation-agent.py');
    const testInput = {
        file_analysis: {
            format: 'csv',
            confidence: 0.8,
            structure: { type: 'structured', encoding: 'utf-8' },
            metadata: { size: 1024, filename: 'test.csv' }
        },
        target_schema: 'asm-1.0.0',
        language: 'python'
    };
    
    return new Promise((resolve) => {
        console.log('🔄 Calling Python converter generation agent...');
        
        const python = spawn('python', [agentPath, JSON.stringify(testInput)], {
            shell: true
        });
        
        let stdout = '';
        let stderr = '';
        
        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        python.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(stdout);
                    console.log('✅ Converter agent call successful');
                    console.log('📊 Agent:', result.agent);
                    console.log('🎯 Success:', result.success);
                    console.log('🔧 Language:', result.language);
                } catch (error) {
                    console.log('❌ Failed to parse converter response');
                    console.log('Raw output:', stdout);
                }
            } else {
                console.log('❌ Converter agent failed with code:', code);
                console.log('Error output:', stderr);
            }
            resolve();
        });
        
        python.on('error', (error) => {
            console.log('💥 Failed to spawn converter agent:', error.message);
            resolve();
        });
    });
}

// Run tests
async function runTests() {
    console.log('=== Testing TypeScript → Python Strands Agent Integration ===\n');
    
    try {
        await testIndividualAgent();
        await testConverterAgent();
        
        console.log('\n🎯 Integration test completed!');
        console.log('📋 Next steps:');
        console.log('  1. If agents work individually, integrate with TypeScript orchestrator');
        console.log('  2. Test with real laboratory data files');
        console.log('  3. Deploy generated converters as Lambda functions');
        
    } catch (error) {
        console.log('💥 Test suite failed:', error.message);
    }
}

if (require.main === module) {
    runTests();
}

module.exports = { testIndividualAgent, testConverterAgent };