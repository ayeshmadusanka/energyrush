#!/usr/bin/env python3
"""
Test Theta Model performance with the new low MAE dataset
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, generate_forecast

def test_theta_model_performance():
    """Test Theta Model with the new optimized dataset"""
    
    with app.app_context():
        print('🧪 TESTING THETA MODEL WITH LOW MAE DATASET')
        print('='*50)
        
        try:
            forecast_result = generate_forecast()
            
            if 'error' in forecast_result:
                print('❌ Error:', forecast_result['error'])
                return False
            else:
                print('✅ Forecast Generated Successfully!')
                print()
                print('📊 PERFORMANCE METRICS:')
                print('-'*30)
                
                # Orders metrics
                orders_r2 = forecast_result.get('orders_r2', 0)
                orders_mae = forecast_result.get('orders_mae', 0)
                
                print('📈 Orders R² Score: {:.3f} ({:.1f}%)'.format(orders_r2, orders_r2*100))
                print('📉 Orders MAE: {:.2f}'.format(orders_mae))
                print('   Target MAE < 5:', '✅ PASS' if orders_mae < 5 else '❌ FAIL')
                print('   Target R² > 85%:', '✅ PASS' if orders_r2 > 0.85 else '❌ FAIL')
                
                print()
                
                # Revenue metrics  
                revenue_r2 = forecast_result.get('revenue_r2', 0)
                revenue_mae = forecast_result.get('revenue_mae', 0)
                
                print('💰 Revenue R² Score: {:.3f} ({:.1f}%)'.format(revenue_r2, revenue_r2*100))
                print('💸 Revenue MAE: ${:.2f}'.format(revenue_mae))
                print('   Target MAE < $300:', '✅ PASS' if revenue_mae < 300 else '❌ FAIL')
                print('   Target R² > 85%:', '✅ PASS' if revenue_r2 > 0.85 else '❌ FAIL')
                
                print()
                print('🎯 OVERALL RESULTS:')
                print('-'*20)
                
                mae_success = orders_mae < 5 and revenue_mae < 300
                r2_success = orders_r2 > 0.85 and revenue_r2 > 0.85
                
                print('✅ MAE Targets Met:', mae_success)
                print('✅ R² Targets Met:', r2_success)
                
                if mae_success and r2_success:
                    print('🎉 SUCCESS! Both MAE and R² targets achieved!')
                    return True
                else:
                    print('⚠️  Some targets not met - dataset may need further adjustment')
                    
                    # Detailed diagnostics
                    print()
                    print('📋 DETAILED DIAGNOSTICS:')
                    print('-'*25)
                    if orders_mae >= 5:
                        print('⚠️  Orders MAE too high: {:.2f} (target < 5)'.format(orders_mae))
                    if revenue_mae >= 300:
                        print('⚠️  Revenue MAE too high: ${:.2f} (target < $300)'.format(revenue_mae))
                    if orders_r2 <= 0.85:
                        print('⚠️  Orders R² too low: {:.1f}% (target > 85%)'.format(orders_r2*100))
                    if revenue_r2 <= 0.85:
                        print('⚠️  Revenue R² too low: {:.1f}% (target > 85%)'.format(revenue_r2*100))
                    
                    return False
                
        except Exception as e:
            print('❌ Testing failed with error:', str(e))
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_theta_model_performance()
    if success:
        print('\n🎊 VALIDATION COMPLETE: Low MAE + High R² achieved!')
    else:
        print('\n🔧 VALIDATION INCOMPLETE: Further dataset optimization needed')