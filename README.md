## Introduction

This code achieves an interface, receiving the POST and GET then scheduling several docker containers where adversarial samples are generated.

Now it implemented to Task 16, docker link and security-enhance modes have been implemented.




## Usage

  * setting with ip and port in gunicorn.conf.py, as follows:

    workers = 5

> worker_class = "gevent"


> bind = "127.0.0.1:5901"  // ip and  port

* using run.sh to start the interface（运行run.sh文件开齐gunicorn服务）:

  chmod a+x run.sh && ./run.sh

## Debug mode

  //in the url blank:

  * for testing mode1 获取被测对象的数据源:

    http://127.0.0.1:5901/test_model

    ```bash
    curl -v -X GET "http://127.0.0.1:5901/test_model" --noproxy 127.0.0.1
    ```

  * for testing mode2 获取内置依赖库及其版本的数据源

    http://127.0.0.1:5901/depn_lib

    ```bash
    curl -v -X GET "http://127.0.0.1:5901/depn_lib" --noproxy 127.0.0.1
    ```

  * for testing mode3 获取被测对象的模型权重文件数量

    http://127.0.0.1:5901/weight_number?test_model=Vgg16

    ```bash
    curl -v -X GET "http://127.0.0.1:5901/weight_number?test_model=Vgg16" --noproxy 127.0.0.1
    ```

  * for testing mode4 被测对象的模型权重文件zip包下载

    http://127.0.0.1:5901/weight_download?test_model=Vgg16

    ```bash
    curl -v -X GET "http://127.0.0.1:5901/weight_download?test_model=Vgg16" -o "Vgg16_weights.zip" --noproxy 127.0.0.1
    ```

  * for testing mode5 获取被测对象的模型权重文件列表、对抗方法列表的数据源

    http://127.0.0.1:5901/check_model?test_model=Vgg16

    ```bash
    curl -v -X GET "http://127.0.0.1:5901/check_model?test_model=Vgg16" --noproxy 127.0.0.1
    ```


  * for testing mode6 启动对抗样本生成

    * leveraging curl for POST:

```shell
curl -X POST http://127.0.0.1:5901/adver_gen \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "mission_id=123&test_model=Vgg16&test_weight=weightA&test_seed=seed1&test_method=FGSM&timeout=3600"  \
--noproxy 127.0.0.1     ***if you has set proxy, this option should be added***
```

  * for testing mode7 对抗样本生成过程中数据轮询

    http://127.0.0.1:5901/adver_gen?mission_id=123

  * for testing mode8 停止对抗样本生成

```shell
curl -X POST http://127.0.0.1:5901/adver_gen_stop \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "mission_id=123" \
--noproxy 127.0.0.1    
```

* for testing mode9 生成的对抗样本zip包下载

  http://127.0.0.1:5901/adver_gen_download?mission_id=321

* for testing mode10 获取不同被测对象下的评估配置指标

  http://127.0.0.1:5901/adver_metrics?test_model=Vgg16

  * for testing mode11 启动测试任务评估

```shell
curl -X POST http://127.0.0.1:5901/adver_eval \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "mission_id=123&eval_metric=abc" \
--noproxy 127.0.0.1    
```

  * for testing mode12 评估过程中数据轮询

    http://127.0.0.1:5901/adver_eval?mission_id=123

  * for testing mode13 启动安全加固任务

```shell
curl -X POST http://127.0.0.1:5901/sec_enhance \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "enhance_id=777&test_model=Vgg16&mission_id=12" \
--noproxy 127.0.0.1    
```

  * for testing mode14 安全加固过程数据轮询

    http://127.0.0.1:5901/sec_enhance?enhance_id=123

## 调试运行tips：

现版本代码需要调试运行的话请将 interface_main.py中model6-model8中的诸如：

```
        model_dict = init_read_yaml_for_model_duplicate()

        docker_shell_run = model_dict[test_model].get('docker_container_run_shell')

        container_id, script_path = docker_shell_run.split(":", 1)

        shell_command = f"{script_path} {test_model} {test_weight} {test_seed} {test_method}"

        shell_path = f"{container_id}:{shell_command}"

        exec_docker_container_shell(shell_path)
```

这部分代码注释掉后（后端还未对接docker引擎）即可正常的调试运行。

若当前后端存在docker引擎的运行环境，即可使用对应的curl命令进行调试，注意参数--noproxy 127.0.0.1最好加上，不然可能会报错

调试运行之前注意yaml文件中各个路径等参数的配置，特别是诸如docker_id之类的，随环境变化而变化的部分，如：

```yaml
weight_download_addr: 5334338a5dfe:/usr/weight.txt
```

这里的5334338a5dfe就要改成自己docker环境的docker_id