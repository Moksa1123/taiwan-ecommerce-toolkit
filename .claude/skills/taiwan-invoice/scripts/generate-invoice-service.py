#!/usr/bin/env python3
"""
快速生成新的發票服務商實作模板

使用方法:
    python generate-invoice-service.py NewProvider

這會生成:
    - lib/services/newprovider-invoice-service.ts
    - 包含所有必要的介面實作
"""

import sys
import os
from pathlib import Path


TEMPLATE = """import crypto from 'crypto'
import { InvoiceService, InvoiceIssueData, InvoiceIssueResponse, InvoiceVoidResponse, InvoicePrintResponse } from './invoice-provider'
import { prisma } from '@/lib/prisma'

export class {ClassName}InvoiceService implements InvoiceService {{
    private API_BASE_URL: string
    private TEST_API_URL = 'https://test.{provider}.com/api'
    private PROD_API_URL = 'https://api.{provider}.com'

    constructor(isProd: boolean = false) {{
        this.API_BASE_URL = isProd ? this.PROD_API_URL : this.TEST_API_URL
    }}

    /**
     * 取得使用者的發票設定
     */
    private async getUserInvoiceSettings(userId: string) {{
        const settings = await prisma.invoiceSettings.findUnique({{
            where: {{ userId }},
        }})

        if (!settings || !settings.{provider}ApiKey) {{
            throw new Error('{ProviderName} 發票設定不完整')
        }}

        return settings
    }}

    /**
     * 開立發票
     */
    async issueInvoice(userId: string, data: InvoiceIssueData): Promise<InvoiceIssueResponse> {{
        try {{
            const settings = await this.getUserInvoiceSettings(userId)
            const isB2B = data.IsB2B === true

            // TODO: 實作 API 請求邏輯
            // 1. 準備資料
            // 2. 加密/簽章
            // 3. 發送請求
            // 4. 解析回應

            const apiData = {{
                // TODO: 填入 API 參數
            }}

            const response = await fetch(`${{this.API_BASE_URL}}/issue`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(apiData),
            }})

            const result = await response.json()

            return {{
                success: result.code === 0,
                code: result.code,
                msg: result.message,
                invoiceNumber: result.invoice_number,
                randomNumber: result.random_number,
                raw: result,
            }}
        }} catch (error) {{
            console.error('[{ProviderName}] 開立發票失敗:', error)
            throw error
        }}
    }}

    /**
     * 作廢發票
     */
    async voidInvoice(userId: string, invoiceNumber: string, reason: string): Promise<InvoiceVoidResponse> {{
        try {{
            const settings = await this.getUserInvoiceSettings(userId)

            // TODO: 實作作廢邏輯

            return {{
                success: true,
                msg: '發票作廢成功',
            }}
        }} catch (error) {{
            console.error('[{ProviderName}] 作廢發票失敗:', error)
            throw error
        }}
    }}

    /**
     * 列印發票
     */
    async printInvoice(userId: string, invoiceNumber: string): Promise<InvoicePrintResponse> {{
        try {{
            const settings = await this.getUserInvoiceSettings(userId)

            // TODO: 實作列印邏輯
            // 根據服務商特性回傳不同類型:
            // - type: 'html' - 回傳 HTML 內容
            // - type: 'redirect' - 回傳 URL 跳轉
            // - type: 'form' - 回傳表單資料

            return {{
                success: true,
                type: 'redirect',
                printUrl: `${{this.API_BASE_URL}}/print?invoice=${{invoiceNumber}}`,
            }}
        }} catch (error) {{
            console.error('[{ProviderName}] 列印發票失敗:', error)
            throw error
        }}
    }}

    /**
     * 輔助方法：計算金額
     */
    private calculateAmounts(totalAmount: number, isB2B: boolean) {{
        if (isB2B) {{
            const taxAmount = Math.round(totalAmount - (totalAmount / 1.05))
            const salesAmount = totalAmount - taxAmount
            return {{ salesAmount, taxAmount, totalAmount }}
        }} else {{
            return {{ salesAmount: totalAmount, taxAmount: 0, totalAmount }}
        }}
    }}

    /**
     * 輔助方法：加密/簽章
     */
    private generateSignature(data: any, secret: string): string {{
        // TODO: 實作加密/簽章邏輯
        // 範例: MD5
        const signString = JSON.stringify(data) + secret
        return crypto.createHash('md5').update(signString).digest('hex')
    }}
}}
"""


def generate_service(provider_name: str):
    """生成服務檔案"""
    # 轉換名稱格式
    class_name = provider_name.capitalize()
    provider_lower = provider_name.lower()

    # 生成內容
    content = TEMPLATE.format(
        ClassName=class_name,
        ProviderName=provider_name,
        provider=provider_lower,
    )

    # 輸出檔案
    output_file = f"{provider_lower}-invoice-service.ts"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] 已生成服務檔案: {output_file}")
    print(f"\n接下來的步驟:")
    print(f"1. 編輯 {output_file}，實作 API 邏輯")
    print(f"2. 在 InvoiceServiceFactory 註冊服務")
    print(f"3. 在 Prisma schema 新增 InvoiceProvider enum")
    print(f"4. 執行 prisma migrate 或 db push")
    print(f"5. 更新前端設定頁面")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python generate-invoice-service.py <ProviderName>")
        print("範例: python generate-invoice-service.py NewProvider")
        sys.exit(1)

    provider = sys.argv[1]
    generate_service(provider)
