#!/usr/bin/perl
# 説明   : flow のタイトル、説明、デフォルトのログイン情報と配置を更新する。
# 作成者 : 江野高広
# 作成日 : 2015/05/16
# 更新   : 2016/01/28 enable password をログイン情報ファイルから外す。
# 更新   : 2018/06/27 user, password を追加。
# 更新   : 2018/10/05 作成するファイルのパーミッションを664 に。

use strict;
use warnings;

use CGI;
use JSON;

use lib '/usr/local/TelnetmanWF/lib';
use Common_system;
use Common_sub;
use Access2DB;
use TelnetmanWF_common;

my $time = time;

my $cgi = new CGI;

#
# DB アクセスのためのオブジェクトを作成する。
#
my ($DB_name, $DB_host, $DB_user, $DB_password) = &Common_system::DB_connect_parameter();
my @DB_connect_parameter_list                   = ('dbi:mysql:' . $DB_name . ':' . $DB_host, $DB_user, $DB_password);
my $access2db                                   = Access2DB -> open(@DB_connect_parameter_list);
$access2db -> log_file(&Common_system::file_sql_log());



#
# パスワードが正しいか確認。
#
my $ref_auth = &TelnetmanWF_common::authorize($cgi, $access2db);

if($ref_auth -> {'result'} == 0){
 my $json_results = &JSON::to_json($ref_auth);
 
 print "Content-type: text/plain; charset=UTF-8\n\n";
 print $json_results;
 
 $access2db -> write_log(&TelnetmanWF_common::prefix_log('root'));
 $access2db -> close;
 exit(0);
}

my $flow_id = $ref_auth -> {'flow_id'};



#
# 配置データを受け取る。
#
my $json_flow_data = $cgi -> param('flow_data');
my $ref_flow_data = &JSON::from_json($json_flow_data);

my $start_data    = $ref_flow_data -> {"start_data"};
my $goal_data     = $ref_flow_data -> {"goal_data"};
my $paper_height  = $ref_flow_data -> {"paper_height"};
my $work_list     = $ref_flow_data -> {"work_list"};
my $case_list     = $ref_flow_data -> {"case_list"};
my $terminal_list = $ref_flow_data -> {"terminal_list"};

my $start_x             = $start_data -> {"x"};
my $start_y             = $start_data -> {"y"};
my $start_link_target   = $start_data -> {"start_link_target"};
my $start_link_vertices = $start_data -> {"start_link_vertices"};

my $goal_x = $goal_data -> {"x"}; 
my $goal_y = $goal_data -> {"y"}; 

my $json_start_link_target   = &JSON::to_json($start_link_target);
my $json_start_link_vertices = &JSON::to_json($start_link_vertices);



#
# flow のタイトル、説明、デフォルトのログイン情報を受取る。
#
my $box_id                       = $cgi -> param('box_id');
my $flow_description             = $cgi -> param('flow_description');
my $default_login_info_file_name = $cgi -> param('default_login_info_file_name');
my $default_login_info_data      = $cgi -> param('default_login_info_data');
my $user                         = $cgi -> param('user');
my $password                     = $cgi -> param('password');
my $enable_password              = $cgi -> param('enable_password');

unless(defined($user)){
 $user = '';
}

unless(defined($password)){
 $password = '';
}

unless(defined($enable_password)){
 $enable_password = '';
}

my $encoded_password        = &TelnetmanWF_common::encode_password($password);
my $encoded_enable_password = &TelnetmanWF_common::encode_password($enable_password);



#
# T_Flow の更新
#
my @set = (
 "vcFlowDescription = '" . &Common_sub::escape_sql($flow_description) . "'",
 'iX = ' . $start_x,
 'iY = ' . $start_y,
 "vcStartLinkTarget = '" . $json_start_link_target . "'",
 "txStartLinkVertices = '" . $json_start_link_vertices . "'",
 'iGoalX = ' . $goal_x,
 'iGoalY = ' . $goal_y,
 'iPaperHieght = ' . $paper_height,
 "vcLoginInfo = '" . &Common_sub::escape_sql($default_login_info_file_name) . "'",
 "vcUser = '" . &Common_sub::escape_sql($user) . "'",
 "vcPassword = '" . &Common_sub::escape_sql($encoded_password) . "'",
 "vcEnablePassword = '" . &Common_sub::escape_sql($encoded_enable_password) . "'"
);
my $table     = 'T_Flow';
my $condition = "where vcFlowId = '" . $flow_id . "'";
$access2db -> set_update(\@set, $table, $condition);
my $count = $access2db -> update_exe;



#
# T_Work の更新
#
while(my ($work_id, $ref_work_data) = each(%$work_list)){
 my $work_x                = $ref_work_data -> {'x'};
 my $work_y                = $ref_work_data -> {'y'};
 my $ok_link_target        = $ref_work_data -> {'ok_link_target'};
 my $ng_link_target        = $ref_work_data -> {'ng_link_target'};
 my $through_link_target   = $ref_work_data -> {'through_link_target'};
 my $ok_link_vertices      = $ref_work_data -> {'ok_link_vertices'};
 my $ng_link_vertices      = $ref_work_data -> {'ng_link_vertices'};
 my $through_link_vertices = $ref_work_data -> {'through_link_vertices'};
 
 my $json_ok_link_target        = &JSON::to_json($ok_link_target);
 my $json_ng_link_target        = &JSON::to_json($ng_link_target);
 my $json_through_link_target   = &JSON::to_json($through_link_target);
 my $json_ok_link_vertices      = &JSON::to_json($ok_link_vertices);
 my $json_ng_link_vertices      = &JSON::to_json($ng_link_vertices);
 my $json_through_link_vertices = &JSON::to_json($through_link_vertices);
 
 my @set = (
  'iX = ' . $work_x,
  'iY = ' . $work_y,
  "vcOkLinkTarget = '" . $json_ok_link_target . "'",
  "vcNgLinkTarget = '" . $json_ng_link_target . "'",
  "vcThroughTarget = '" . $json_through_link_target . "'",
  "txOkLinkVertices = '" . $json_ok_link_vertices . "'",
  "txNgLinkVertices = '" . $json_ng_link_vertices . "'",
  "txThroughVertices = '" . $json_through_link_vertices . "'"
 );
 
 my $table     = 'T_Work';
 my $condition = "where vcFlowId = '" . $flow_id . "' and vcWorkId = '" . $work_id . "'";
 $access2db -> set_update(\@set, $table, $condition);
 my $count = $access2db -> update_exe;
}



#
# T_Case の更新
#
while(my ($case_id, $ref_case_data) = each(%$case_list)){
 my $case_x             = $ref_case_data -> {'x'};
 my $case_y             = $ref_case_data -> {'y'};
 my $link_target_list   = $ref_case_data -> {'link_target_list'};
 my $link_vertices_list = $ref_case_data -> {'link_vertices_list'};
 
 my $json_link_target_list   = &JSON::to_json($link_target_list);
 my $json_link_vertices_list = &JSON::to_json($link_vertices_list);
 
 my @set = (
  'iX = ' . $case_x,
  'iY = ' . $case_y,
  "txLinkTargetList = '" . $json_link_target_list . "'",
  "txLinkVerticesList = '" . $json_link_vertices_list . "'"
 );
 
 my $table     = 'T_Case';
 my $condition = "where vcFlowId = '" . $flow_id . "' and vcCaseId = '" . $case_id . "'";
 $access2db -> set_update(\@set, $table, $condition);
 my $count = $access2db -> update_exe;
}



#
# T_Terminal の更新
#
while(my ($terminal_id, $ref_terminal_data) = each(%$terminal_list)){
 my $terminal_x = $ref_terminal_data -> {'x'};
 my $terminal_y = $ref_terminal_data -> {'y'};
 
 my @set = (
  'iX = ' . $terminal_x,
  'iY = ' . $terminal_y
 );
 
 my $table     = 'T_Terminal';
 my $condition = "where vcFlowId = '" . $flow_id . "' and vcTerminalId = '" . $terminal_id . "'";
 $access2db -> set_update(\@set, $table, $condition);
 my $count = $access2db -> update_exe;
}

$access2db -> write_log(&TelnetmanWF_common::prefix_log('root'));
$access2db -> close;

#
# loginInfo の更新
#
my $file_default_login_info = &Common_system::file_default_login_info($flow_id);

if((length($default_login_info_file_name) == 0) && (-f $file_default_login_info)){
 unlink($file_default_login_info);
}
elsif((length($default_login_info_file_name) > 0) && (length($default_login_info_data) > 0)){
 open(DLOGIN, '>', $file_default_login_info);
 flock(DLOGIN, 2);
 print DLOGIN $default_login_info_data;
 close(DLOGIN);
 
 umask(0002);
 chmod(0664, $file_default_login_info);
}



my %results = (
 'result'      => 1,
 'flow_id'     => $flow_id,
 'box_id'      => $box_id,
 'update_time' => $time
);

my $json_results = &JSON::to_json(\%results);

print "Content-type: text/plain; charset=UTF-8\n\n";
print $json_results;
