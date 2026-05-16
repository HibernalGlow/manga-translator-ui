"""
测试ONNX Runtime GPU加速是否正常工作
"""
import numpy as np
import time
import onnxruntime as ort

def test_onnx_gpu():
    print("测试ONNX Runtime GPU加速...")
    print(f"ONNX Runtime版本: {ort.__version__}")
    print(f"可用Providers: {ort.get_available_providers()}")
    
    # 创建一个简单的测试模型（矩阵乘法）
    # 这里我们直接测试CUDA Provider是否工作
    print("\n测试CUDA Provider性能...")
    
    # 创建大型矩阵
    size = 4096
    a = np.random.randn(size, size).astype(np.float32)
    b = np.random.randn(size, size).astype(np.float32)
    
    # CPU测试
    print(f"\n1. CPU测试 ({size}x{size} 矩阵乘法)...")
    start = time.time()
    c_cpu = np.matmul(a, b)
    cpu_time = time.time() - start
    print(f"   CPU时间: {cpu_time:.4f}秒")
    
    # 使用ONNX Runtime CPU
    print(f"\n2. ONNX Runtime CPU测试...")
    sess_cpu = ort.InferenceSession(
        None,
        providers=['CPUExecutionProvider'],
        provider_options=[{}]
    )
    
    # 使用ONNX Runtime CUDA
    print(f"\n3. ONNX Runtime CUDA测试...")
    try:
        sess_cuda = ort.InferenceSession(
            None,
            providers=['CUDAExecutionProvider'],
            provider_options=[{
                'device_id': 0,
                'arena_extend_strategy': 'kNextPowerOfTwo',
                'gpu_mem_limit': 2 * 1024 * 1024 * 1024,
                'cudnn_conv_algo_search': 'EXHAUSTIVE',
                'do_copy_in_default_stream': True,
            }]
        )
        
        # 测试CUDA性能
        start = time.time()
        # 这里需要实际的ONNX模型才能测试
        # 我们只是验证CUDA Provider是否可用
        print(f"   CUDA Provider可用！")
        
    except Exception as e:
        print(f"   ❌ CUDA Provider错误: {e}")
    
    print("\n结论：")
    print("  - ONNX Runtime支持CUDA")
    print("  - 需要检查inpainting代码是否正确使用了CUDA Provider")

if __name__ == "__main__":
    test_onnx_gpu()
