import matlab.engine

# import customized matlab functions
# https://au.mathworks.com/help/matlab/matlab_external/call-user-script-and-function-from-python.html
mat_eng = matlab.engine.start_matlab() 
mat_eng.cd(r'./code/matlab_code', nargout=0)

print(f'Matlab function vessel_jerman found at: {mat_eng.which("vessel_jerman")}')