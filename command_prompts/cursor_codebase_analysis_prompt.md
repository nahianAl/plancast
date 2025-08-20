# Comprehensive Codebase Analysis & Bug Detection Prompt

Please perform a thorough analysis of the entire codebase to identify potential bugs, errors, and areas for improvement. Focus on the following areas:

## 🔍 Bug Detection & Error Analysis

### Critical Issues
- **Runtime Errors**: Identify null pointer exceptions, undefined variable access, array out-of-bounds errors
- **Logic Errors**: Detect incorrect conditional statements, infinite loops, unreachable code
- **Memory Issues**: Find memory leaks, buffer overflows, improper resource cleanup
- **Concurrency Issues**: Race conditions, deadlocks, thread safety violations
- **Error Handling**: Missing try-catch blocks, unhandled exceptions, improper error propagation

### Code Quality Issues
- **Type Safety**: Type mismatches, implicit conversions that could fail
- **Variable Scope**: Unused variables, shadowed variables, improper scoping
- **Function Design**: Functions that are too long, have too many parameters, or lack clear purpose
- **Dead Code**: Unreachable code blocks, unused imports/dependencies

## 🏗️ Architecture & Design Harmony

### Consistency Checks
- **Naming Conventions**: Ensure consistent variable, function, class, and file naming
- **Code Style**: Verify adherence to established coding standards and formatting
- **Pattern Usage**: Check for consistent implementation of design patterns
- **API Design**: Ensure consistent parameter ordering, return types, error handling

### Structural Analysis
- **Dependency Management**: Circular dependencies, unnecessary dependencies, missing dependencies
- **Module Organization**: Proper separation of concerns, cohesive modules
- **Abstraction Levels**: Appropriate use of interfaces, abstract classes, and inheritance
- **Configuration Management**: Hardcoded values that should be configurable

## 🛡️ Robustness & Reliability

### Input Validation
- **Data Sanitization**: Check for proper input validation and sanitization
- **Boundary Conditions**: Edge cases, empty inputs, maximum/minimum values
- **User Input**: XSS prevention, SQL injection protection, CSRF protection

### Performance Considerations
- **Algorithmic Efficiency**: Identify inefficient algorithms, O(n²) operations that could be optimized
- **Resource Usage**: Memory usage patterns, file handle management, database connections
- **Caching**: Opportunities for caching, cache invalidation issues

### Security Analysis
- **Authentication & Authorization**: Proper access controls, secure token handling
- **Data Protection**: Sensitive data exposure, encryption usage
- **Network Security**: Secure communication protocols, API endpoint security

## 📋 Specific Analysis Tasks

1. **Cross-Reference Analysis**: Identify inconsistencies between related components
2. **Data Flow Tracking**: Trace data flow to find potential corruption points
3. **State Management**: Check for proper state initialization and cleanup
4. **Integration Points**: Analyze external API calls, database interactions, file operations
5. **Testing Coverage**: Identify untested code paths and missing test scenarios

## 📊 Output Format

For each issue found, please provide:
- **File and Line Number**: Exact location of the issue
- **Severity Level**: Critical, High, Medium, Low
- **Issue Category**: Bug, Performance, Security, Maintainability, Style
- **Description**: Clear explanation of the problem
- **Impact**: How this affects the application
- **Recommended Fix**: Specific suggestions for resolution
- **Code Example**: Show the problematic code and suggested improvement

## 🎯 Priority Focus Areas

Please prioritize analysis in this order:
1. **Security vulnerabilities** and **data integrity issues**
2. **Runtime errors** and **crash-causing bugs**
3. **Performance bottlenecks** and **scalability issues**
4. **Maintainability** and **code organization problems**
5. **Style consistency** and **documentation gaps**

## Additional Considerations

- Check for **backwards compatibility** issues if applicable
- Verify **database schema consistency** with code models
- Analyze **API contract compliance** between services
- Review **logging and monitoring** implementation
- Assess **error reporting** and **debugging capabilities**

Please scan the entire codebase systematically and provide a comprehensive report with actionable recommendations for improving code quality, fixing bugs, and maintaining architectural harmony.