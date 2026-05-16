"""
Inpainting性能测试脚本
测试不同配置在CPU和GPU下的速度对比
"""
import asyncio
import time
import torch
import numpy as np
from PIL import Image

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manga_translator.inpainting import dispatch as dispatch_inpainting
from manga_translator.inpainting import prepare as prepare_inpainting
from manga_translator.config import Inpainter, InpainterConfig, InpaintPrecision


def create_test_image_and_mask(size=(2048, 2048)):
    """创建测试图像和掩码"""
    # 创建随机图像
    image = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
    
    # 创建掩码（中间区域）
    mask = np.zeros(size, dtype=np.uint8)
    center_x, center_y = size[1] // 2, size[0] // 2
    mask_size = min(size) // 4
    mask[center_y - mask_size:center_y + mask_size, 
         center_x - mask_size:center_x + mask_size] = 255
    
    return image, mask


async def test_inpainting_config(inpainter_type: Inpainter, 
                                   precision: InpaintPrecision,
                                   force_torch: bool,
                                   device: str,
                                   test_name: str,
                                   inpainting_size: int = 2048):
    """测试单个inpainting配置"""
    print(f"\n{'='*60}")
    print(f"测试配置: {test_name}")
    print(f"  Inpainter: {inpainter_type.value}")
    print(f"  Precision: {precision.value}")
    print(f"  Force Torch: {force_torch}")
    print(f"  Inpainting Size: {inpainting_size}")
    print(f"  Device: {device}")
    print(f"{'='*60}")
    
    # 创建测试数据
    print("创建测试图像和掩码...")
    image, mask = create_test_image_and_mask()
    
    # 准备配置
    config = InpainterConfig(
        inpainter=inpainter_type,
        inpainting_size=inpainting_size,
        inpainting_precision=precision,
        force_use_torch_inpainting=force_torch
    )
    
    # 准备模型
    print("加载模型...")
    start_load = time.time()
    await prepare_inpainting(inpainter_type, device)
    load_time = time.time() - start_load
    print(f"模型加载时间: {load_time:.2f}秒")
    
    # 检查实际使用的设备
    if force_torch:
        print(f"✅ 强制使用PyTorch模式")
        if device == 'cuda':
            print(f"   目标设备: {device}")
            print(f"   CUDA可用: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"   GPU名称: {torch.cuda.get_device_name(0)}")
    else:
        print(f"✅ 使用ONNX Runtime模式")
        if device == 'cuda':
            try:
                import onnxruntime as ort
                print(f"   ONNX Runtime可用Providers: {ort.get_available_providers()}")
            except:
                pass
    
    # 执行inpainting
    print("执行inpainting...")
    start_inpaint = time.time()
    result = await dispatch_inpainting(
        inpainter_type,
        image,
        mask,
        config,
        inpainting_size=inpainting_size,
        device=device
    )
    inpaint_time = time.time() - start_inpaint
    
    print(f"✅ Inpainting时间: {inpaint_time:.2f}秒")
    print(f"   总时间（加载+推理）: {load_time + inpaint_time:.2f}秒")
    
    return {
        'test_name': test_name,
        'inpainter': inpainter_type.value,
        'precision': precision,
        'force_torch': force_torch,
        'device': device,
        'load_time': load_time,
        'inpaint_time': inpaint_time,
        'total_time': load_time + inpaint_time
    }


async def run_all_tests():
    """运行所有测试"""
    results = []
    
    # 测试配置1: lama_mpe + fp16 + 强制torch + 2048
    config1 = {
        'inpainter_type': Inpainter.lama_mpe,
        'precision': InpaintPrecision.fp16,
        'force_torch': True,
        'inpainting_size': 2048,
        'test_name': 'PyTorch + 2048'
    }
    
    # 测试配置2: lama_mpe + fp16 + ONNX + 1024
    config2 = {
        'inpainter_type': Inpainter.lama_mpe,
        'precision': InpaintPrecision.fp16,
        'force_torch': False,
        'inpainting_size': 1024,
        'test_name': 'ONNX + 1024'
    }
    
    # 检查GPU是否可用
    gpu_available = torch.cuda.is_available()
    print(f"\nGPU可用: {gpu_available}")
    if gpu_available:
        print(f"GPU名称: {torch.cuda.get_device_name(0)}")
    
    # 只测试GPU（如果可用）
    device = 'cuda' if gpu_available else 'cpu'
    
    # 运行所有测试组合
    configs = [config1, config2]
    
    for config in configs:
        try:
            result = await test_inpainting_config(
                inpainter_type=config['inpainter_type'],
                precision=config['precision'],
                force_torch=config['force_torch'],
                device=device,
                test_name=config['test_name'],
                inpainting_size=config['inpainting_size']
            )
            results.append(result)
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 打印结果汇总
    print("\n" + "="*80)
    print("性能测试结果汇总")
    print("="*80)
    print(f"{'测试配置':<40} {'设备':<8} {'加载时间':<12} {'推理时间':<12} {'总时间':<12}")
    print("-"*80)
    for r in results:
        print(f"{r['test_name']:<40} {r['device']:<8} {r['load_time']:<12.2f} {r['inpaint_time']:<12.2f} {r['total_time']:<12.2f}")
    
    # 计算加速比
    if len(results) >= 4:
        print("\n" + "="*80)
        print("加速比分析")
        print("="*80)
        
        # GPU vs CPU 加速比
        for i in range(0, len(results), 2):
            if i + 1 < len(results):
                cpu_result = results[i]
                gpu_result = results[i + 1]
                speedup = cpu_result['inpaint_time'] / gpu_result['inpaint_time']
                print(f"{cpu_result['test_name'].split(' @')[0]}:")
                print(f"  GPU加速比: {speedup:.2f}x (推理时间)")
        
        # 配置2 vs 配置1 加速比
        if len(results) >= 4:
            config1_cpu = results[0]
            config2_cpu = results[2]
            config1_gpu = results[1]
            config2_gpu = results[3]
            
            print(f"\n配置2 vs 配置1:")
            print(f"  CPU加速比: {config1_cpu['inpaint_time'] / config2_cpu['inpaint_time']:.2f}x")
            print(f"  GPU加速比: {config1_gpu['inpaint_time'] / config2_gpu['inpaint_time']:.2f}x")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
